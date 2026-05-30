from __future__ import annotations

import json
import re
from typing import Any

import requests


DEFAULT_FALLBACK_ERROR = "AI review failed, fallback to rule-based review."
SEVERITY_WEIGHT = {"High": 3, "Medium": 2, "Low": 1}
PRIORITY_FILE_KEYWORDS = (
    "auth",
    "login",
    "permission",
    "jwt",
    "token",
    "security",
    "middleware",
    "config",
    ".env",
    "settings",
    "requirements",
    "package.json",
    ".github/workflows",
    "dockerfile",
    "deploy",
)


class LLMReviewer:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.2,
        timeout: int = 30,
        max_input_chars: int = 20000,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "").strip().rstrip("/")
        self.model = (model or "").strip()
        self.temperature = temperature
        self.timeout = timeout
        self.max_input_chars = max(2000, max_input_chars)
        self.last_prompt_metadata: dict[str, Any] = {
            "ai_context_file_count": 0,
            "top_risk_file_count": 0,
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def build_review_prompt(
        self,
        pr: dict[str, Any],
        files: list[dict[str, Any]],
        risks: list[dict[str, Any]],
        risk_summary: dict[str, Any],
        stats: dict[str, Any],
    ) -> list[dict[str, str]]:
        prioritized_files = self._prioritize_files(files, risks)
        file_context = self._build_file_context(prioritized_files)
        risk_context = self._build_risk_context(risks)
        top_risk_files = self._top_risk_files(risks)

        self.last_prompt_metadata = {
            "ai_context_file_count": len(file_context),
            "top_risk_file_count": len(top_risk_files),
        }

        prompt_payload = {
            "pr": {
                "title": pr.get("title", ""),
                "number": pr.get("number"),
                "state": pr.get("state", ""),
                "author": pr.get("author", ""),
                "base_branch": pr.get("base_branch", ""),
                "head_branch": pr.get("head_branch", ""),
            },
            "stats": stats,
            "risk_summary": risk_summary,
            "review_focus": self._build_review_focus(prioritized_files, risks),
            "context_notice": {
                "patch_truncated_file_count": sum(1 for item in files if item.get("patch_truncated")),
                "ai_context_file_count": len(file_context),
                "top_risk_file_count": len(top_risk_files),
            },
            "files": file_context,
            "risks": risk_context,
        }
        prompt_payload = self._fit_payload_to_budget(prompt_payload)
        context_notice = prompt_payload.get("context_notice", {})
        self.last_prompt_metadata["ai_context_file_count"] = int(context_notice.get("ai_context_file_count", 0) or 0)
        self.last_prompt_metadata["top_risk_file_count"] = int(context_notice.get("top_risk_file_count", 0) or 0)

        system_message = (
            "你是一名资深代码评审工程师，需要根据 PR 元信息、关键 diff 片段和规则命中结果给出专业评审结论。"
            "你的目标不是机械罗列风险，而是像真实 reviewer 一样先判断影响面，再指出最值得追问的问题，再给出可执行建议。"
            "输出必须是 JSON 对象，不要输出 Markdown 代码块，不要输出额外解释。"
            "JSON 必须包含以下字段："
            "pr_summary(字符串), main_changes(字符串数组), risk_analysis(字符串数组), "
            "review_suggestions(字符串数组), overall_risk_level(High|Medium|Low), confidence(High|Medium|Low)。"
            "要求："
            "1. 语言使用中文，表达专业、自然、像资深 reviewer，而不是模板化口号。"
            "2. 只基于给定上下文作答，禁止编造不存在的文件、风险或业务背景。"
            "3. 如果存在不确定性，可以明确指出需要补看的上下文，但表述必须具体。"
            "4. 风险分析优先解释影响和触发条件，不要只是重复规则名称。"
            "5. 如果规则未发现明显高风险，也要给出有价值的人工复核建议。"
        )

        user_message = (
            "请基于以下 JSON 数据生成评审结果。输出严格为 JSON：\n"
            f"{json.dumps(prompt_payload, ensure_ascii=False)}"
        )

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def generate_review(
        self,
        pr: dict[str, Any],
        files: list[dict[str, Any]],
        risks: list[dict[str, Any]],
        risk_summary: dict[str, Any],
        stats: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.is_configured():
            return self._build_fallback(
                pr=pr,
                risk_summary=risk_summary,
                error="AI config is missing, fallback to rule-based review.",
            )

        messages = self.build_review_prompt(pr, files, risks, risk_summary, stats)
        request_url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": messages,
        }

        try:
            response = requests.post(
                request_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)
        except requests.exceptions.RequestException:
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        if not 200 <= response.status_code < 300:
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        try:
            response_data = response.json()
            content = (((response_data.get("choices") or [{}])[0].get("message") or {}).get("content", ""))
        except (ValueError, AttributeError, IndexError, TypeError):
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        parsed = self._parse_model_json(content)
        if parsed is None:
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        normalized = self._normalize_ai_output(parsed, pr=pr, risk_summary=risk_summary)
        normalized["enabled"] = True
        normalized["error"] = None
        return normalized

    def _build_file_context(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []

        budget = self.max_input_chars
        selected: list[dict[str, Any]] = []

        for file_item in files:
            patch = (file_item.get("patch") or "")[:3200]
            base_item = {
                "filename": file_item.get("filename", ""),
                "status": file_item.get("status", "unknown"),
                "additions": int(file_item.get("additions", 0) or 0),
                "deletions": int(file_item.get("deletions", 0) or 0),
                "changes": int(file_item.get("changes", 0) or 0),
                "patch_truncated": bool(file_item.get("patch_truncated", False)),
                "patch": patch,
            }

            serialized = json.dumps(base_item, ensure_ascii=False)
            if len(serialized) <= budget:
                selected.append(base_item)
                budget -= len(serialized)
                continue

            no_patch_item = {**base_item, "patch": ""}
            no_patch_len = len(json.dumps(no_patch_item, ensure_ascii=False))
            if no_patch_len >= budget:
                break

            remaining_for_patch = max(0, budget - no_patch_len)
            trimmed_item = {**base_item, "patch": patch[:remaining_for_patch]}
            selected.append(trimmed_item)
            budget = 0
            break

        return selected

    def _fit_payload_to_budget(self, payload: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized) <= self.max_input_chars:
            return payload

        files = list(payload.get("files", []))
        while len(serialized) > self.max_input_chars and files:
            files.pop()
            payload["files"] = files
            payload["context_notice"]["ai_context_file_count"] = len(files)
            serialized = json.dumps(payload, ensure_ascii=False)

        risks = list(payload.get("risks", []))
        while len(serialized) > self.max_input_chars and len(risks) > 8:
            risks.pop()
            payload["risks"] = risks
            payload["context_notice"]["top_risk_file_count"] = len({risk.get("file") for risk in risks if risk.get("file")})
            serialized = json.dumps(payload, ensure_ascii=False)

        if len(serialized) > self.max_input_chars:
            payload["review_focus"] = payload.get("review_focus", [])[:3]
            serialized = json.dumps(payload, ensure_ascii=False)

        if len(serialized) > self.max_input_chars:
            payload["pr"] = {
                "title": str(payload.get("pr", {}).get("title", ""))[:200],
                "number": payload.get("pr", {}).get("number"),
                "state": payload.get("pr", {}).get("state", ""),
                "author": payload.get("pr", {}).get("author", ""),
                "base_branch": payload.get("pr", {}).get("base_branch", ""),
                "head_branch": payload.get("pr", {}).get("head_branch", ""),
            }

        return payload

    def _prioritize_files(self, files: list[dict[str, Any]], risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []

        risk_scores: dict[str, int] = {}
        for risk in risks:
            filename = risk.get("file")
            if not filename:
                continue
            risk_scores[filename] = risk_scores.get(filename, 0) + SEVERITY_WEIGHT.get(str(risk.get("severity", "")), 0)

        def score(file_item: dict[str, Any]) -> tuple[int, int, int, str]:
            filename = str(file_item.get("filename", ""))
            lowered = filename.lower()
            keyword_score = 1 if any(keyword in lowered for keyword in PRIORITY_FILE_KEYWORDS) else 0
            risk_score = risk_scores.get(filename, 0)
            change_score = int(file_item.get("changes", 0) or 0)
            truncated_score = 1 if file_item.get("patch_truncated") else 0
            return (risk_score, keyword_score + truncated_score, change_score, filename)

        return sorted(files, key=score, reverse=True)

    @staticmethod
    def _build_review_focus(files: list[dict[str, Any]], risks: list[dict[str, Any]]) -> list[str]:
        focus_points: list[str] = []
        top_risks = sorted(risks, key=lambda item: SEVERITY_WEIGHT.get(str(item.get("severity", "")), 0), reverse=True)[:5]
        for risk in top_risks:
            risk_file = risk.get("file") or "PR-level"
            focus_points.append(f"{risk_file}: {risk.get('type', '')} - {risk.get('message', '')}")

        for file_item in files[:3]:
            filename = file_item.get("filename", "")
            changes = int(file_item.get("changes", 0) or 0)
            if not filename:
                continue
            focus_points.append(f"{filename}: changed_lines={changes}")

        deduped: list[str] = []
        seen: set[str] = set()
        for item in focus_points:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)
        return deduped[:6]

    @staticmethod
    def _build_risk_context(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sorted_risks = sorted(
            risks,
            key=lambda item: SEVERITY_WEIGHT.get(str(item.get("severity", "")), 0),
            reverse=True,
        )
        return [
            {
                "file": risk.get("file"),
                "line": risk.get("line"),
                "severity": risk.get("severity", ""),
                "type": risk.get("type", ""),
                "message": risk.get("message", ""),
                "evidence": risk.get("evidence", ""),
                "suggestion": risk.get("suggestion", ""),
            }
            for risk in sorted_risks[:50]
        ]

    @staticmethod
    def _top_risk_files(risks: list[dict[str, Any]]) -> set[str]:
        return {str(risk.get("file")) for risk in risks if risk.get("file") and risk.get("severity") in {"High", "Medium"}}

    @staticmethod
    def _parse_model_json(content: str) -> dict[str, Any] | None:
        raw = (content or "").strip()
        if not raw:
            return None

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE | re.DOTALL).strip()
        try:
            data = json.loads(fenced)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return None

        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_ai_output(payload: dict[str, Any], pr: dict[str, Any], risk_summary: dict[str, Any]) -> dict[str, Any]:
        overall_risk_level = str(payload.get("overall_risk_level", "Medium")).strip() or "Medium"
        confidence = str(payload.get("confidence", "Medium")).strip() or "Medium"

        if overall_risk_level not in {"High", "Medium", "Low"}:
            overall_risk_level = "Medium"
        if confidence not in {"High", "Medium", "Low"}:
            confidence = "Medium"

        pr_summary = str(payload.get("pr_summary", "")).strip()
        if not pr_summary:
            pr_summary = LLMReviewer._default_summary(pr, risk_summary)

        return {
            "enabled": True,
            "error": None,
            "pr_summary": pr_summary,
            "main_changes": LLMReviewer._coerce_string_list(payload.get("main_changes")),
            "risk_analysis": LLMReviewer._coerce_string_list(payload.get("risk_analysis")),
            "review_suggestions": LLMReviewer._coerce_string_list(payload.get("review_suggestions")),
            "overall_risk_level": overall_risk_level,
            "confidence": confidence,
        }

    @staticmethod
    def _coerce_string_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _default_summary(pr: dict[str, Any], risk_summary: dict[str, Any]) -> str:
        title = pr.get("title", "当前 PR")
        total = int(risk_summary.get("total", 0) or 0)
        high = int(risk_summary.get("high", 0) or 0)
        if total == 0:
            return f"PR《{title}》当前没有命中明显高风险规则，但仍建议结合业务上下文确认关键路径是否完整覆盖。"
        return f"PR《{title}》命中了 {total} 项风险提示，其中 High 风险 {high} 项，建议优先核查高影响代码路径。"

    @staticmethod
    def _build_fallback(pr: dict[str, Any], risk_summary: dict[str, Any], error: str) -> dict[str, Any]:
        title = pr.get("title", "当前 PR")
        total = int(risk_summary.get("total", 0) or 0)
        high_count = int(risk_summary.get("high", 0) or 0)
        medium_count = int(risk_summary.get("medium", 0) or 0)

        if high_count > 0:
            overall_risk_level = "High"
        elif medium_count > 0:
            overall_risk_level = "Medium"
        else:
            overall_risk_level = "Low"

        if total == 0:
            summary = f"PR《{title}》已完成规则审查。当前未发现明显高风险信号，但仍建议人工确认关键业务路径。"
        else:
            summary = (
                f"PR《{title}》已完成规则审查。当前识别到 {total} 项风险提示，"
                f"其中 High 风险 {high_count} 项；AI 总结不可用，建议按规则结果继续人工复核。"
            )

        return {
            "enabled": False,
            "error": error,
            "pr_summary": summary,
            "main_changes": [],
            "risk_analysis": [],
            "review_suggestions": [],
            "overall_risk_level": overall_risk_level,
            "confidence": "Low",
        }
