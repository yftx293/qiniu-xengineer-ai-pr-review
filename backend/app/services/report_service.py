from __future__ import annotations

from typing import Any


class ReportService:
    def build_markdown_report(
        self,
        pr: dict[str, Any],
        stats: dict[str, Any],
        files: list[dict[str, Any]],
        summary: str,
        risks: list[dict[str, Any]],
        suggestions: list[str],
        risk_summary: dict[str, Any],
        analysis_trace: dict[str, Any],
        ai_review: dict[str, Any] | None,
    ) -> str:
        final_summary = summary
        if ai_review and ai_review.get("enabled") and ai_review.get("pr_summary"):
            final_summary = ai_review.get("pr_summary", summary)

        main_changes = self._pick_main_changes(ai_review, files)
        review_suggestions = self._pick_suggestions(ai_review, suggestions)

        lines: list[str] = []
        lines.append("# AI PR Review Report")
        lines.append("")
        lines.append("## 1. PR 基本信息")
        lines.append(f"- 标题: {pr.get('title', '')}")
        lines.append(f"- 作者: {pr.get('author', '')}")
        lines.append(f"- 状态: {pr.get('state', '')}")
        lines.append(f"- 分支: {pr.get('head_branch', '')} -> {pr.get('base_branch', '')}")
        lines.append(f"- 文件数: {stats.get('file_count', 0)}")
        lines.append(
            f"- additions / deletions: {stats.get('total_additions', 0)} / {stats.get('total_deletions', 0)}"
        )
        lines.append("")

        lines.append("## 2. 变更总结")
        lines.append(final_summary or "暂无总结。")
        lines.append("")

        lines.append("## 3. 主要变更")
        if main_changes:
            for item in main_changes:
                lines.append(f"- {item}")
        else:
            lines.append("- 暂无可展示的主要变更。")
        lines.append("")

        lines.append("## 4. 风险概览")
        lines.append(f"- total: {risk_summary.get('total', 0)}")
        lines.append(f"- high: {risk_summary.get('high', 0)}")
        lines.append(f"- medium: {risk_summary.get('medium', 0)}")
        lines.append(f"- low: {risk_summary.get('low', 0)}")
        lines.append(f"- has_blocking_risk: {risk_summary.get('has_blocking_risk', False)}")
        lines.append("")

        lines.append("## 5. 风险详情")
        lines.append(self.format_risk_table(risks))
        lines.append("")

        lines.append("## 6. Review 建议")
        if review_suggestions:
            for item in review_suggestions:
                lines.append(f"- {item}")
        else:
            lines.append("- 暂无建议。")
        lines.append("")

        lines.append("## 7. 分析链路")
        lines.append(f"- context_source: {analysis_trace.get('context_source', 'unknown')}")
        lines.append(f"- ai_status: {analysis_trace.get('ai_status', 'unknown')}")
        lines.append(f"- patch 截断文件数: {analysis_trace.get('patch_truncated_file_count', 0)}")

        rule_hits = analysis_trace.get("rule_hits_by_type", {}) or {}
        if rule_hits:
            lines.append("- rule_hits_by_type:")
            for risk_type, count in sorted(rule_hits.items()):
                lines.append(f"  - {risk_type}: {count}")
        else:
            lines.append("- rule_hits_by_type: none")
        lines.append("")

        lines.append("## 8. 分析限制")
        lines.append("- GitHub API 可能受未认证 rate limit 影响。")
        lines.append("- 超长 patch 会被截断，极大 PR 的上下文可能不完整。")
        lines.append("- AI 结果仅作辅助参考，最终仍需人工确认。")
        lines.append("")

        lines.append("## 9. 说明")
        lines.append(
            "本报告由规则分析和可选 AI 生成，仅作为辅助 Review 参考，最终仍需人工确认后再做合并决策。"
        )

        ai_section = self.format_ai_review(ai_review)
        if ai_section:
            lines.append("")
            lines.append(ai_section)

        return "\n".join(lines)

    def format_risk_table(self, risks: list[dict[str, Any]]) -> str:
        if not risks:
            return "未识别到风险项。"

        lines = [
            "| Severity | Confidence | File | Type | Evidence | Suggestion |",
            "| --- | --- | --- | --- | --- | --- |",
        ]

        for risk in risks:
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._escape_cell(risk.get("severity", "")),
                        self._escape_cell(risk.get("confidence", "")),
                        self._escape_cell(risk.get("file") or "PR-level"),
                        self._escape_cell(risk.get("type", "")),
                        self._escape_cell(risk.get("evidence") or ""),
                        self._escape_cell(risk.get("suggestion", "")),
                    ]
                )
                + " |"
            )

        return "\n".join(lines)

    def format_ai_review(self, ai_review: dict[str, Any] | None) -> str:
        if not ai_review:
            return ""

        lines = ["## 附加: AI Review 状态"]
        lines.append(f"- enabled: {ai_review.get('enabled', False)}")

        error = ai_review.get("error")
        if error:
            lines.append(f"- error: {error}")

        risk_level = ai_review.get("overall_risk_level")
        confidence = ai_review.get("confidence")
        if risk_level:
            lines.append(f"- overall_risk_level: {risk_level}")
        if confidence:
            lines.append(f"- confidence: {confidence}")

        return "\n".join(lines)

    def _pick_main_changes(self, ai_review: dict[str, Any] | None, files: list[dict[str, Any]]) -> list[str]:
        if ai_review and ai_review.get("enabled") and ai_review.get("main_changes"):
            return [str(item) for item in ai_review.get("main_changes", []) if str(item).strip()]

        result: list[str] = []
        for file_item in files[:10]:
            filename = file_item.get("filename", "")
            status = file_item.get("status", "unknown")
            additions = int(file_item.get("additions", 0) or 0)
            deletions = int(file_item.get("deletions", 0) or 0)
            result.append(f"{filename} ({status}, +{additions}/-{deletions})")
        return result

    def _pick_suggestions(self, ai_review: dict[str, Any] | None, rule_suggestions: list[str]) -> list[str]:
        if ai_review and ai_review.get("enabled") and ai_review.get("review_suggestions"):
            return [str(item) for item in ai_review.get("review_suggestions", []) if str(item).strip()]
        return rule_suggestions

    @staticmethod
    def _escape_cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()
