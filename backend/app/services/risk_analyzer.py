from __future__ import annotations

import re
from typing import Any


SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

SECRET_PATTERN = re.compile(
    r"\b(api_key|apikey|secret|token|password|passwd|private_key|access_key)\b",
    re.IGNORECASE,
)
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete)\b", re.IGNORECASE)
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|TEMP)\b", re.IGNORECASE)

DEPENDENCY_FILE_NAMES = (
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pom.xml",
    "build.gradle",
    "pyproject.toml",
)
CONFIG_KEYWORDS = (
    ".env",
    "config",
    "settings",
    "application.yml",
    "application.yaml",
    "application.properties",
    "docker-compose",
)
AUTH_KEYWORDS = ("auth", "login", "permission", "jwt", "token", "security", "middleware")


class RiskAnalyzer:
    def analyze_files(self, files: list[dict[str, Any]], parsed_diffs: list[dict[str, Any]]) -> dict[str, Any]:
        collected: list[dict[str, Any]] = []

        for file_item, parsed_diff in zip(files, parsed_diffs):
            collected.extend(self.analyze_file(file_item, parsed_diff))

        collected.extend(self._analyze_missing_tests(files))
        deduped = self._dedupe_risks(collected)
        sorted_risks = sorted(deduped, key=lambda item: SEVERITY_ORDER.get(item["severity"], 99))

        return {
            "risks": sorted_risks,
            "suggestions": self.build_suggestions(sorted_risks),
            "risk_summary": self.build_risk_summary(sorted_risks),
            "rule_hits_by_type": self.build_rule_hits_by_type(sorted_risks),
        }

    def analyze_file(self, file_item: dict[str, Any], parsed_diff: dict[str, Any]) -> list[dict[str, Any]]:
        filename = file_item.get("filename", "")
        additions = int(file_item.get("additions", 0) or 0)
        deletions = int(file_item.get("deletions", 0) or 0)
        added_lines = parsed_diff.get("added_lines", [])

        risks: list[dict[str, Any]] = []
        risks.extend(self._detect_hardcoded_secret(filename, added_lines))
        risks.extend(self._detect_dangerous_functions(filename, added_lines))
        risks.extend(self._detect_exception_swallowing(filename, added_lines))
        risks.extend(self._detect_sql_injection(filename, added_lines))
        risks.extend(self._detect_todo_fixme(filename, added_lines))
        risks.extend(self._detect_dependency_change(filename))
        risks.extend(self._detect_config_change(filename))
        risks.extend(self._detect_auth_related_change(filename))
        risks.extend(self._detect_large_change(filename, additions + deletions))
        return risks

    def build_suggestions(self, risks: list[dict[str, Any]]) -> list[str]:
        if not risks:
            return []

        suggestions: list[str] = []
        severities = {risk["severity"] for risk in risks}
        types = {risk["type"] for risk in risks}

        if "High" in severities:
            suggestions.append("建议优先处理 High 风险项，确认是否存在安全或稳定性问题。")
        if "Dangerous Function Usage" in types:
            suggestions.append("建议移除或严格隔离危险执行函数，避免引入命令执行风险。")
        if "Potential SQL Injection" in types:
            suggestions.append("建议使用参数化查询，避免字符串拼接 SQL。")
        if "Missing Tests" in types or "Large Change Set" in types:
            suggestions.append("建议为本次较大变更补充测试用例，并覆盖关键路径。")
        if "Hardcoded Secret" in types:
            suggestions.append("建议将密钥和凭据改为从环境变量或安全配置中心读取。")

        if not suggestions:
            suggestions.append("建议对中低风险项进行二次人工 Review，确认变更影响面。")
        return suggestions

    def build_risk_summary(self, risks: list[dict[str, Any]]) -> dict[str, Any]:
        high = sum(1 for risk in risks if risk["severity"] == "High")
        medium = sum(1 for risk in risks if risk["severity"] == "Medium")
        low = sum(1 for risk in risks if risk["severity"] == "Low")
        return {
            "total": len(risks),
            "high": high,
            "medium": medium,
            "low": low,
            "has_blocking_risk": high > 0,
        }

    def build_rule_hits_by_type(self, risks: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for risk in risks:
            risk_type = str(risk.get("type", "")).strip()
            if not risk_type:
                continue
            counts[risk_type] = counts.get(risk_type, 0) + 1
        return counts

    def _detect_hardcoded_secret(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for line in added_lines:
            content = line.get("content", "")
            if not SECRET_PATTERN.search(content):
                continue

            confidence = "High" if self._looks_like_assignment(content) else "Medium"
            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="High",
                    risk_type="Hardcoded Secret",
                    message="疑似存在硬编码密钥或敏感字段。",
                    evidence=content,
                    suggestion="建议改为从环境变量或安全配置中心读取。",
                    confidence=confidence,
                )
            )
        return risks

    def _detect_dangerous_functions(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for line in added_lines:
            content = line.get("content", "")
            lowered = content.lower()
            matched = (
                "eval(" in lowered
                or "exec(" in lowered
                or "os.system(" in lowered
                or ("subprocess" in lowered and "shell=true" in lowered.replace(" ", ""))
            )
            if not matched:
                continue

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="High",
                    risk_type="Dangerous Function Usage",
                    message="检测到高风险执行函数，可能导致命令注入或远程执行风险。",
                    evidence=content,
                    suggestion="建议使用安全替代方案，并避免 shell=True 或动态执行不可信输入。",
                    confidence="High",
                )
            )
        return risks

    def _detect_exception_swallowing(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        for idx, line in enumerate(added_lines):
            content = line.get("content", "").strip()
            lowered = content.lower()

            if lowered in {"except: pass", "except exception: pass"}:
                risks.append(
                    self._risk_item(
                        file=filename,
                        line=line.get("line_no"),
                        severity="Medium",
                        risk_type="Swallowed Exception",
                        message="异常被直接吞掉，可能掩盖真实错误并增加排障难度。",
                        evidence=line.get("content", ""),
                        suggestion="建议记录异常日志并给出明确处理策略，避免仅 pass。",
                        confidence="Medium",
                    )
                )
                continue

            if lowered.startswith("except") and lowered.endswith(":"):
                next_line = added_lines[idx + 1].get("content", "").strip().lower() if idx + 1 < len(added_lines) else ""
                if next_line == "pass":
                    risks.append(
                        self._risk_item(
                            file=filename,
                            line=line.get("line_no"),
                            severity="Medium",
                            risk_type="Swallowed Exception",
                            message="except 代码块仅包含 pass，异常处理不完整。",
                            evidence=f"{line.get('content', '')} ... pass",
                            suggestion="建议至少记录日志并补充恢复或失败处理逻辑。",
                            confidence="Medium",
                        )
                    )

        return risks

    def _detect_sql_injection(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        for line in added_lines:
            content = line.get("content", "")
            lowered = content.lower()

            if not SQL_PATTERN.search(content):
                continue
            if not (
                " + " in content
                or "format(" in lowered
                or "%" in content
                or 'f"' in content
                or "f'" in content
            ):
                continue

            severity = "High" if " + " in content or 'f"' in content or "f'" in content else "Medium"
            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity=severity,
                    risk_type="Potential SQL Injection",
                    message="检测到 SQL 语句可能通过字符串拼接或插值构造，存在注入风险。",
                    evidence=content,
                    suggestion="建议改用参数化查询，避免动态拼接 SQL。",
                    confidence="Medium",
                )
            )

        return risks

    def _detect_dependency_change(self, filename: str) -> list[dict[str, Any]]:
        lowered = filename.lower()
        if not any(name in lowered for name in DEPENDENCY_FILE_NAMES):
            return []

        return [
            self._risk_item(
                file=filename,
                line=None,
                severity="Medium",
                risk_type="Dependency Change",
                message="检测到依赖清单文件变更，可能引入兼容性或供应链风险。",
                evidence=filename,
                suggestion="建议核对依赖版本变更说明并执行依赖安全扫描。",
                confidence="High",
            )
        ]

    def _detect_config_change(self, filename: str) -> list[dict[str, Any]]:
        lowered = filename.lower()
        if not any(keyword in lowered for keyword in CONFIG_KEYWORDS):
            return []

        return [
            self._risk_item(
                file=filename,
                line=None,
                severity="Medium",
                risk_type="Configuration Change",
                message="检测到配置文件变更，可能影响运行时行为或环境安全。",
                evidence=filename,
                suggestion="建议逐项确认配置差异，并在目标环境进行回归验证。",
                confidence="High",
            )
        ]

    def _detect_auth_related_change(self, filename: str) -> list[dict[str, Any]]:
        lowered = filename.lower()
        if not any(keyword in lowered for keyword in AUTH_KEYWORDS):
            return []

        return [
            self._risk_item(
                file=filename,
                line=None,
                severity="Medium",
                risk_type="Auth/Permission Sensitive Change",
                message="检测到认证或权限相关模块变更，需重点关注越权或鉴权绕过风险。",
                evidence=filename,
                suggestion="建议补充权限边界测试和负向用例，确认访问控制逻辑正确。",
                confidence="Medium",
            )
        ]

    def _detect_large_change(self, filename: str, changed_lines: int) -> list[dict[str, Any]]:
        if changed_lines < 300:
            return []

        return [
            self._risk_item(
                file=filename,
                line=None,
                severity="Medium",
                risk_type="Large Change Set",
                message="单文件改动较大，可能增加回归风险和 Review 难度。",
                evidence=f"changed_lines={changed_lines}",
                suggestion="建议拆分提交或补充更细粒度测试，降低合并风险。",
                confidence="High",
            )
        ]

    def _detect_todo_fixme(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for line in added_lines:
            content = line.get("content", "")
            if not TODO_PATTERN.search(content):
                continue

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="Low",
                    risk_type="TODO/FIXME Marker",
                    message="新增代码包含 TODO/FIXME/HACK/TEMP 标记，可能表示未完成逻辑。",
                    evidence=content,
                    suggestion="建议在合并前确认该标记是否可清理，或补充明确跟踪任务。",
                    confidence="High",
                )
            )

        return risks

    def _analyze_missing_tests(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []

        has_test_file = any(
            any(keyword in (item.get("filename", "").lower()) for keyword in ("test", "tests", "spec"))
            for item in files
        )
        total_changed = sum(int(item.get("additions", 0) or 0) + int(item.get("deletions", 0) or 0) for item in files)

        if has_test_file or total_changed < 50:
            return []

        return [
            self._risk_item(
                file=None,
                line=None,
                severity="Medium",
                risk_type="Missing Tests",
                message="本次 PR 变更较多但未发现测试文件改动，可能存在回归风险。",
                evidence=f"total_changed={total_changed}",
                suggestion="建议补充测试用例（单元/集成）覆盖主要改动路径。",
                confidence="High",
            )
        ]

    @staticmethod
    def _looks_like_assignment(content: str) -> bool:
        return "=" in content and any(marker in content for marker in ('"', "'", "Bearer ", "token", "secret"))

    @staticmethod
    def _risk_item(
        file: str | None,
        line: int | None,
        severity: str,
        risk_type: str,
        message: str,
        evidence: str | None,
        suggestion: str,
        confidence: str,
    ) -> dict[str, Any]:
        return {
            "file": file,
            "line": line,
            "severity": severity,
            "type": risk_type,
            "message": message,
            "evidence": RiskAnalyzer._truncate_evidence(evidence),
            "suggestion": suggestion,
            "confidence": confidence,
        }

    @staticmethod
    def _truncate_evidence(evidence: str | None) -> str | None:
        if evidence is None:
            return None
        if len(evidence) <= 200:
            return evidence
        return f"{evidence[:200]}..."

    @staticmethod
    def _dedupe_risks(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[tuple[str | None, str, str | None]] = set()

        for risk in risks:
            key = (risk.get("file"), risk.get("type", ""), risk.get("evidence"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(risk)

        return unique
