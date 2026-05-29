from app.services.report_service import ReportService


def test_build_markdown_report_uses_ai_summary_when_enabled() -> None:
    report = ReportService().build_markdown_report(
        pr={
            "title": "Improve login flow",
            "author": "alice",
            "state": "open",
            "head_branch": "feat/login",
            "base_branch": "main",
        },
        stats={"file_count": 1, "total_additions": 10, "total_deletions": 2},
        files=[{"filename": "auth.py", "status": "modified", "additions": 10, "deletions": 2}],
        summary="Rule summary",
        risks=[],
        suggestions=["Add tests"],
        risk_summary={"total": 0, "high": 0, "medium": 0, "low": 0, "has_blocking_risk": False},
        ai_review={
            "enabled": True,
            "error": None,
            "pr_summary": "AI summary",
            "main_changes": ["auth.py (+10/-2)"],
            "review_suggestions": ["Verify auth edge cases"],
            "overall_risk_level": "Low",
            "confidence": "High",
        },
    )

    assert "AI summary" in report
    assert "Verify auth edge cases" in report
    assert "未识别到风险项" in report


def test_build_markdown_report_falls_back_to_rule_suggestions() -> None:
    report = ReportService().build_markdown_report(
        pr={
            "title": "Update deps",
            "author": "bob",
            "state": "open",
            "head_branch": "chore/deps",
            "base_branch": "main",
        },
        stats={"file_count": 1, "total_additions": 4, "total_deletions": 1},
        files=[{"filename": "requirements.txt", "status": "modified", "additions": 4, "deletions": 1}],
        summary="Rule summary",
        risks=[
            {
                "severity": "Medium",
                "confidence": "High",
                "file": "requirements.txt",
                "type": "Dependency Change",
                "evidence": "requirements.txt",
                "suggestion": "Run dependency audit",
            }
        ],
        suggestions=["Run dependency audit"],
        risk_summary={"total": 1, "high": 0, "medium": 1, "low": 0, "has_blocking_risk": False},
        ai_review=None,
    )

    assert "Rule summary" in report
    assert "Run dependency audit" in report
    assert "| Medium | High | requirements.txt | Dependency Change |" in report
