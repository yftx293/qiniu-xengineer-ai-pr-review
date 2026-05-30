from __future__ import annotations

import re
from typing import Any


SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

SECRET_PATTERN = re.compile(
    r"\b(api_key|apikey|secret|token|password|passwd|private_key|access_key|client_secret)\b",
    re.IGNORECASE,
)
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete)\b", re.IGNORECASE)
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|TEMP)\b", re.IGNORECASE)
SECRET_SAMPLE_VALUE_PATTERN = re.compile(
    r"\b(example|sample|demo|dummy|mock|test|placeholder|changeme|redacted)\b",
    re.IGNORECASE,
)
SENSITIVE_LOG_PATTERN = re.compile(
    r"\b(password|passwd|secret|token|authorization|cookie|session|api[_-]?key)\b",
    re.IGNORECASE,
)
SQL_EXECUTION_PATTERN = re.compile(r"\b(execute|executemany|query|raw|run)\s*\(", re.IGNORECASE)

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
AUTH_KEYWORDS = (
    "auth",
    "login",
    "permission",
    "jwt",
    "token",
    "security",
    "middleware",
    "session",
    "oauth",
    "rbac",
)
INFRA_KEYWORDS = (
    ".github/workflows",
    "dockerfile",
    "helm",
    "terraform",
    "infra",
    "deploy",
    "k8s",
    "chart",
    "ci",
)
STYLE_FILE_EXTENSIONS = (".css", ".scss", ".sass", ".less")
DOC_FILE_EXTENSIONS = (".md", ".mdx", ".txt", ".rst")
TEST_FILE_KEYWORDS = ("test", "tests", "spec")


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
        deleted_lines = parsed_diff.get("deleted_lines", [])
        changed_lines = additions + deletions

        risks: list[dict[str, Any]] = []
        risks.extend(self._detect_hardcoded_secret(filename, added_lines))
        risks.extend(self._detect_dangerous_functions(filename, added_lines))
        risks.extend(self._detect_exception_swallowing(filename, added_lines))
        risks.extend(self._detect_sql_injection(filename, added_lines))
        risks.extend(self._detect_sensitive_logging(filename, added_lines))
        risks.extend(self._detect_todo_fixme(filename, added_lines))
        risks.extend(self._detect_test_weakening(filename, file_item, deleted_lines))
        risks.extend(self._detect_dependency_change(filename))
        risks.extend(self._detect_config_change(filename))
        risks.extend(self._detect_auth_related_change(filename))
        risks.extend(self._detect_infra_change(filename))
        risks.extend(self._detect_large_change(filename, changed_lines))
        return risks

    def build_suggestions(self, risks: list[dict[str, Any]]) -> list[str]:
        if not risks:
            return []

        suggestions: list[str] = []
        severities = {risk["severity"] for risk in risks}
        types = {risk["type"] for risk in risks}

        if "High" in severities:
            suggestions.append("建议先处理 High 风险项，再决定是否继续合并，避免高风险问题被后续噪音掩盖。")
        if "Hardcoded Secret" in types or "Sensitive Data Logging" in types:
            suggestions.append("建议复核敏感信息的读取、传递和打印链路，确保凭据不会直接出现在代码、日志或返回值中。")
        if "Dangerous Function Usage" in types:
            suggestions.append("建议确认危险执行入口是否可被外部输入影响，必要时改用白名单参数和非 shell 模式。")
        if "Potential SQL Injection" in types:
            suggestions.append("建议将动态 SQL 改为参数化查询，并确认输入在进入数据库层前已经过约束或转义。")
        if "Missing Tests" in types or "Test Coverage Regression" in types or "Large Change Set" in types:
            suggestions.append("建议为关键改动补充回归测试，尤其覆盖权限边界、异常路径和高改动文件。")
        if "Auth/Permission Sensitive Change" in types:
            suggestions.append("建议补充鉴权失败、越权访问和角色边界的负向用例，确认权限变更不会放宽访问范围。")
        if "CI/Deploy Sensitive Change" in types or "Configuration Change" in types:
            suggestions.append("建议在目标环境复核配置和发布流水线差异，确认运行参数、密钥注入和部署步骤未被意外改变。")

        if not suggestions:
            suggestions.append("建议结合业务上下文进行二次人工 Review，重点确认规则未覆盖到的语义风险。")
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
            if self._should_ignore_secret_line(filename, content):
                continue

            confidence = "High" if self._looks_like_real_secret_assignment(content) else "Medium"
            message = "疑似将敏感凭据直接写入代码。若该值来自真实环境，会带来泄露和轮换困难。"
            suggestion = "建议改为从环境变量、密钥管理服务或运行时注入配置读取，并确认示例值不会进入生产分支。"

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="High",
                    risk_type="Hardcoded Secret",
                    message=message,
                    evidence=content,
                    suggestion=suggestion,
                    confidence=confidence,
                )
            )
        return risks

    def _detect_dangerous_functions(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for line in added_lines:
            content = line.get("content", "")
            lowered = content.lower()
            compact = lowered.replace(" ", "")

            matched = False
            message = ""
            suggestion = ""
            confidence = "Medium"

            if "eval(" in lowered or "exec(" in lowered:
                matched = True
                message = "检测到动态执行代码逻辑。若执行内容受外部输入影响，容易引入远程执行风险。"
                suggestion = "建议避免直接使用 eval/exec；如确有必要，应限制可执行内容并建立严格白名单。"
                confidence = "High"
            elif "os.system(" in lowered:
                matched = True
                message = "检测到通过 shell 执行命令。若参数未做约束，可能引入命令注入风险。"
                suggestion = "建议改用参数列表调用或更安全的库能力，并确认命令参数不直接拼接用户输入。"
                confidence = "High"
            elif "subprocess" in lowered and "shell=true" in compact:
                matched = True
                message = "检测到 subprocess 使用 shell=True。若命令拼接了动态输入，风险通常高于普通子进程调用。"
                suggestion = "建议优先使用 shell=False 和参数数组；如必须开启 shell，应显式过滤输入来源。"
                confidence = "High"

            if not matched:
                continue

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="High",
                    risk_type="Dangerous Function Usage",
                    message=message,
                    evidence=content,
                    suggestion=suggestion,
                    confidence=confidence,
                )
            )
        return risks

    def _detect_exception_swallowing(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        for idx, line in enumerate(added_lines):
            content = line.get("content", "").strip()
            lowered = content.lower()

            if lowered in {"except: pass", "except exception: pass", "except baseexception: pass"}:
                risks.append(
                    self._risk_item(
                        file=filename,
                        line=line.get("line_no"),
                        severity="Medium",
                        risk_type="Swallowed Exception",
                        message="异常被直接吞掉，真实故障会被隐藏，后续排障和告警定位都会变困难。",
                        evidence=line.get("content", ""),
                        suggestion="建议至少记录异常上下文，并明确决定是降级处理、重试还是向上抛出。",
                        confidence="High",
                    )
                )
                continue

            if lowered.startswith("except") and lowered.endswith(":"):
                next_line = added_lines[idx + 1].get("content", "").strip().lower() if idx + 1 < len(added_lines) else ""
                if next_line in {"pass", "..."}:
                    risks.append(
                        self._risk_item(
                            file=filename,
                            line=line.get("line_no"),
                            severity="Medium",
                            risk_type="Swallowed Exception",
                            message="except 代码块没有形成有效处理逻辑，异常路径可能被静默吞掉。",
                            evidence=f"{line.get('content', '')} ... {next_line}",
                            suggestion="建议补充日志、指标或失败处理逻辑，避免异常路径在运行时悄悄失效。",
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

            has_dynamic_sql = any(marker in content for marker in (" + ", "%")) or (
                "format(" in lowered or 'f"' in content or "f'" in content
            )
            if not has_dynamic_sql and not SQL_EXECUTION_PATTERN.search(content):
                continue
            if self._looks_like_parameterized_sql(content):
                continue

            severity = "High" if " + " in content or 'f"' in content or "f'" in content else "Medium"
            message = "检测到 SQL 语句可能通过字符串拼接或插值构造。若变量来自外部输入，存在注入风险。"
            suggestion = "建议改为参数化查询或 ORM 安全占位写法，并确认查询条件不会直接拼接到原始 SQL 中。"

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity=severity,
                    risk_type="Potential SQL Injection",
                    message=message,
                    evidence=content,
                    suggestion=suggestion,
                    confidence="Medium",
                )
            )

        return risks

    def _detect_sensitive_logging(self, filename: str, added_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for line in added_lines:
            content = line.get("content", "")
            lowered = content.lower()
            if not any(marker in lowered for marker in ("print(", "logger.", "logging.", "console.log(", "debug(")):
                continue
            if not SENSITIVE_LOG_PATTERN.search(content):
                continue

            risks.append(
                self._risk_item(
                    file=filename,
                    line=line.get("line_no"),
                    severity="Medium",
                    risk_type="Sensitive Data Logging",
                    message="日志语句疑似输出了敏感字段。即使只在调试环境打印，也可能在收集链路中形成泄露面。",
                    evidence=content,
                    suggestion="建议移除敏感值输出，必要时仅保留脱敏后的标识信息或 trace id。",
                    confidence="Medium",
                )
            )
        return risks

    def _detect_test_weakening(
        self,
        filename: str,
        file_item: dict[str, Any],
        deleted_lines: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        lowered = filename.lower()
        if not self._looks_like_test_file(lowered):
            return []
        if int(file_item.get("deletions", 0) or 0) <= 0:
            return []
        if not deleted_lines:
            return []

        evidence = deleted_lines[0].get("content", "")
        return [
            self._risk_item(
                file=filename,
                line=deleted_lines[0].get("line_no"),
                severity="Medium",
                risk_type="Test Coverage Regression",
                message="测试文件出现删除或弱化迹象，建议确认是否无意降低了回归覆盖范围。",
                evidence=evidence,
                suggestion="建议说明被删测试的替代覆盖方式，或补充等价的新测试确保风险没有被带过。",
                confidence="Medium",
            )
        ]

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
                message="检测到依赖清单文件变更，可能引入兼容性、供应链或运行时行为变化。",
                evidence=filename,
                suggestion="建议核对依赖变更说明、锁定版本差异，并执行依赖安全扫描或最小回归验证。",
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
                message="检测到配置文件变更，运行时行为、环境隔离或敏感参数加载方式可能受到影响。",
                evidence=filename,
                suggestion="建议逐项确认配置差异，并在目标环境验证默认值、密钥注入和回滚路径是否可靠。",
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
                message="检测到认证、会话或权限边界相关变更，这类改动通常需要更严格的越权和失败路径验证。",
                evidence=filename,
                suggestion="建议重点补充权限边界、未登录访问、角色切换和 token 失效等负向用例。",
                confidence="High",
            )
        ]

    def _detect_infra_change(self, filename: str) -> list[dict[str, Any]]:
        lowered = filename.lower()
        if not any(keyword in lowered for keyword in INFRA_KEYWORDS):
            return []

        return [
            self._risk_item(
                file=filename,
                line=None,
                severity="Medium",
                risk_type="CI/Deploy Sensitive Change",
                message="检测到发布流水线或基础设施配置变更，可能影响构建、部署权限或环境行为。",
                evidence=filename,
                suggestion="建议确认部署参数、执行权限和回滚方案，并验证变更不会扩大发布面或暴露敏感步骤。",
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
                message="单文件改动规模较大，Review 盲区和回归风险都会明显上升。",
                evidence=f"changed_lines={changed_lines}",
                suggestion="建议拆分提交、标注重点改动段落，或补充更细粒度测试来降低合并风险。",
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
                    message="新增代码包含 TODO/FIXME/HACK/TEMP 标记，建议确认该逻辑是否适合直接进入主分支。",
                    evidence=content,
                    suggestion="建议在合并前确认该标记是否可以清理，或明确关联后续跟踪任务与处理边界。",
                    confidence="High",
                )
            )

        return risks

    def _analyze_missing_tests(self, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []

        has_test_file = any(self._looks_like_test_file(item.get("filename", "").lower()) for item in files)
        total_changed = sum(int(item.get("additions", 0) or 0) + int(item.get("deletions", 0) or 0) for item in files)

        if has_test_file or total_changed < 50:
            return []
        if all(self._is_low_risk_file_for_missing_tests(item.get("filename", "")) for item in files):
            return []

        auth_or_runtime_sensitive = any(
            any(keyword in item.get("filename", "").lower() for keyword in AUTH_KEYWORDS + CONFIG_KEYWORDS)
            for item in files
        )
        severity = "High" if auth_or_runtime_sensitive and total_changed >= 80 else "Medium"
        confidence = "High" if auth_or_runtime_sensitive or total_changed >= 120 else "Medium"

        return [
            self._risk_item(
                file=None,
                line=None,
                severity=severity,
                risk_type="Missing Tests",
                message="本次 PR 已涉及实质性代码或运行时变更，但没有看到对应测试变更，回归风险偏高。",
                evidence=f"total_changed={total_changed}",
                suggestion="建议补充覆盖关键路径的单元或集成测试，至少覆盖权限、异常和主要业务分支。",
                confidence=confidence,
            )
        ]

    @staticmethod
    def _looks_like_assignment(content: str) -> bool:
        return "=" in content and any(marker in content for marker in ('"', "'", "Bearer ", "token", "secret"))

    @staticmethod
    def _looks_like_real_secret_assignment(content: str) -> bool:
        return RiskAnalyzer._looks_like_assignment(content) and not SECRET_SAMPLE_VALUE_PATTERN.search(content)

    @staticmethod
    def _should_ignore_secret_line(filename: str, content: str) -> bool:
        lowered = content.strip().lower()
        normalized_name = filename.lower()

        if not lowered:
            return True
        if lowered.startswith(("#", "//", "/*", "*", "--")):
            return True
        if normalized_name.endswith(DOC_FILE_EXTENSIONS):
            return True
        if any(marker in lowered for marker in ("logger.", "logging.", "print(", "console.log(")):
            return True
        if RiskAnalyzer._looks_like_test_file(normalized_name) and SECRET_SAMPLE_VALUE_PATTERN.search(content):
            return True
        if "example" in lowered and "=" not in lowered:
            return True
        if SECRET_SAMPLE_VALUE_PATTERN.search(content) and not RiskAnalyzer._looks_like_assignment(content):
            return True
        return False

    @staticmethod
    def _looks_like_parameterized_sql(content: str) -> bool:
        lowered = content.lower()
        return any(marker in lowered for marker in ("execute(query, ", "execute(sql, ", "cursor.execute(sql, params", "text("))

    @staticmethod
    def _looks_like_test_file(filename: str) -> bool:
        return any(keyword in filename for keyword in TEST_FILE_KEYWORDS)

    @staticmethod
    def _is_low_risk_file_for_missing_tests(filename: str) -> bool:
        lowered = filename.lower()
        return lowered.endswith(DOC_FILE_EXTENSIONS + STYLE_FILE_EXTENSIONS) or any(
            marker in lowered for marker in CONFIG_KEYWORDS
        )

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
