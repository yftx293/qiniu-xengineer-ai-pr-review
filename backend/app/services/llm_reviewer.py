from __future__ import annotations

import json
import re
from typing import Any

import requests


DEFAULT_FALLBACK_ERROR = "AI review failed, fallback to rule-based review."


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
        file_context = self._build_file_context(files)
        risk_context = self._build_risk_context(risks)

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
            "files": file_context,
            "risks": risk_context,
        }
        prompt_payload = self._fit_payload_to_budget(prompt_payload)

        system_message = (
            "你是资深代码评审工程师。请根据输入的 PR 信息、文件变更和规则风险识别结果输出评审结论。"
            "输出必须是 JSON 对象，不要输出 Markdown 代码块，不要输出额外解释。"
            "JSON 必须包含以下字段："
            "pr_summary(字符串), main_changes(字符串数组), risk_analysis(字符串数组), "
            "review_suggestions(字符串数组), overall_risk_level(High|Medium|Low), confidence(High|Medium|Low)。"
            "不要编造不存在的文件和风险。"
            "如果风险为空，请说明规则分析未发现明显高风险问题，但仍建议人工 Review。"
            "语言使用中文，表达具体、专业。"
        )

        user_message = (
            "请基于以下 JSON 数据生成评审结果：\n"
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
            content = (
                ((response_data.get("choices") or [{}])[0].get("message") or {}).get("content", "")
            )
        except (ValueError, AttributeError, IndexError, TypeError):
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        parsed = self._parse_model_json(content)
        if parsed is None:
            return self._build_fallback(pr=pr, risk_summary=risk_summary, error=DEFAULT_FALLBACK_ERROR)

        normalized = self._normalize_ai_output(parsed)
        normalized["enabled"] = True
        normalized["error"] = None
        return normalized

    def _build_file_context(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []

        budget = self.max_input_chars
        selected: list[dict[str, Any]] = []

        for file_item in files:
            patch = (file_item.get("patch") or "")[:3000]
            base_item = {
                "filename": file_item.get("filename", ""),
                "status": file_item.get("status", "unknown"),
                "additions": int(file_item.get("additions", 0) or 0),
                "deletions": int(file_item.get("deletions", 0) or 0),
                "changes": int(file_item.get("changes", 0) or 0),
                "patch": patch,
            }

            serialized = json.dumps(base_item, ensure_ascii=False)
            if len(serialized) <= budget:
                selected.append(base_item)
                budget -= len(serialized)
                continue

            # Try to keep the file entry with a shorter patch when budget is low.
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
            serialized = json.dumps(payload, ensure_ascii=False)

        risks = list(payload.get("risks", []))
        while len(serialized) > self.max_input_chars and risks:
            risks.pop()
            payload["risks"] = risks
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

    @staticmethod
    def _build_risk_context(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "file": risk.get("file"),
                "line": risk.get("line"),
                "severity": risk.get("severity", ""),
                "type": risk.get("type", ""),
                "message": risk.get("message", ""),
                "evidence": risk.get("evidence", ""),
            }
            for risk in risks[:50]
        ]

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
    def _normalize_ai_output(payload: dict[str, Any]) -> dict[str, Any]:
        overall_risk_level = str(payload.get("overall_risk_level", "Medium")).strip() or "Medium"
        confidence = str(payload.get("confidence", "Medium")).strip() or "Medium"

        if overall_risk_level not in {"High", "Medium", "Low"}:
            overall_risk_level = "Medium"
        if confidence not in {"High", "Medium", "Low"}:
            confidence = "Medium"

        return {
            "enabled": True,
            "error": None,
            "pr_summary": str(payload.get("pr_summary", "")).strip(),
            "main_changes": [str(item) for item in payload.get("main_changes", []) if str(item).strip()],
            "risk_analysis": [str(item) for item in payload.get("risk_analysis", []) if str(item).strip()],
            "review_suggestions": [
                str(item) for item in payload.get("review_suggestions", []) if str(item).strip()
            ],
            "overall_risk_level": overall_risk_level,
            "confidence": confidence,
        }

    @staticmethod
    def _build_fallback(pr: dict[str, Any], risk_summary: dict[str, Any], error: str) -> dict[str, Any]:
        title = pr.get("title", "this PR")
        high_count = int(risk_summary.get("high", 0) or 0)

        if high_count > 0:
            overall_risk_level = "High"
        elif int(risk_summary.get("medium", 0) or 0) > 0:
            overall_risk_level = "Medium"
        else:
            overall_risk_level = "Low"

        return {
            "enabled": False,
            "error": error,
            "pr_summary": f"PR《{title}》已完成规则分析，AI 结果不可用。",
            "main_changes": [],
            "risk_analysis": [],
            "review_suggestions": [],
            "overall_risk_level": overall_risk_level,
            "confidence": "Low",
        }
