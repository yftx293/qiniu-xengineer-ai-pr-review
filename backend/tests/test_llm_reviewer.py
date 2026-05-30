from app.services.llm_reviewer import LLMReviewer


def _build_reviewer(max_input_chars: int = 1200) -> LLMReviewer:
    return LLMReviewer(
        api_key="key",
        base_url="https://api.openai.com/v1",
        model="gpt-4.1-mini",
        max_input_chars=max_input_chars,
    )


def test_build_review_prompt_prioritizes_risky_files() -> None:
    reviewer = _build_reviewer(max_input_chars=5000)
    files = [
        {
            "filename": "docs/guide.md",
            "status": "modified",
            "additions": 120,
            "deletions": 0,
            "changes": 120,
            "patch": "@@ -1,0 +1,120 @@\n+" + "\n+".join(["docs"] * 120),
            "patch_truncated": False,
        },
        {
            "filename": "backend/app/auth_service.py",
            "status": "modified",
            "additions": 40,
            "deletions": 10,
            "changes": 50,
            "patch": "@@ -1,0 +1,40 @@\n+" + "\n+".join(["token = request.headers.get('Authorization')"] * 40),
            "patch_truncated": True,
        },
    ]
    risks = [
        {
            "file": "backend/app/auth_service.py",
            "line": 10,
            "severity": "High",
            "type": "Auth/Permission Sensitive Change",
            "message": "认证链路发生变更。",
            "evidence": "token = request.headers.get('Authorization')",
            "suggestion": "补充权限边界测试。",
            "confidence": "High",
        }
    ]

    reviewer.build_review_prompt(
        pr={"title": "Improve auth", "number": 1, "state": "open", "author": "alice"},
        files=files,
        risks=risks,
        risk_summary={"total": 1, "high": 1, "medium": 0, "low": 0},
        stats={"file_count": 2, "total_additions": 160, "total_deletions": 10, "total_changes": 170},
    )

    assert reviewer.last_prompt_metadata["top_risk_file_count"] == 1
    assert reviewer.last_prompt_metadata["ai_context_file_count"] >= 1


def test_parse_model_json_accepts_fenced_json() -> None:
    content = """```json
{"pr_summary":"summary","main_changes":["a"],"risk_analysis":["b"],"review_suggestions":["c"],"overall_risk_level":"High","confidence":"Medium"}
```"""

    parsed = LLMReviewer._parse_model_json(content)

    assert parsed is not None
    assert parsed["pr_summary"] == "summary"


def test_normalize_ai_output_adds_default_summary_when_missing() -> None:
    payload = {
        "main_changes": ["Updated auth middleware"],
        "risk_analysis": "需要重点关注 token 校验路径。",
        "review_suggestions": ["补充鉴权失败场景测试"],
        "overall_risk_level": "High",
        "confidence": "High",
    }

    normalized = LLMReviewer._normalize_ai_output(
        payload,
        pr={"title": "Auth refactor"},
        risk_summary={"total": 2, "high": 1, "medium": 1, "low": 0},
    )

    assert "Auth refactor" in normalized["pr_summary"]
    assert normalized["risk_analysis"] == ["需要重点关注 token 校验路径。"]
    assert normalized["review_suggestions"] == ["补充鉴权失败场景测试"]


def test_build_fallback_returns_natural_rule_summary() -> None:
    fallback = LLMReviewer._build_fallback(
        pr={"title": "Checkout hardening"},
        risk_summary={"total": 3, "high": 1, "medium": 2, "low": 0},
        error="AI review failed, fallback to rule-based review.",
    )

    assert fallback["enabled"] is False
    assert "规则审查" in fallback["pr_summary"]
    assert fallback["overall_risk_level"] == "High"
