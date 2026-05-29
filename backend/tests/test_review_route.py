from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.routes import review as review_route
from app.services.github_service import GitHubAPIError


def _sample_context() -> dict[str, object]:
    return {
        "pr": {
            "title": "Add review mode",
            "number": 12,
            "state": "open",
            "author": "alice",
            "html_url": "https://github.com/openai/openai-python/pull/12",
            "base_branch": "main",
            "head_branch": "feat/review-mode",
            "created_at": "2026-05-29T00:00:00Z",
            "updated_at": "2026-05-29T00:10:00Z",
            "additions": 12,
            "deletions": 3,
            "changed_files": 1,
        },
        "files": [
            {
                "filename": "app/review.py",
                "status": "modified",
                "additions": 12,
                "deletions": 3,
                "changes": 15,
                "raw_url": "",
                "blob_url": "",
                "patch": """@@ -1,0 +1,2 @@
+api_key = "demo-secret"
+print("review")
""",
                "patch_truncated": False,
            }
        ],
        "stats": {
            "file_count": 1,
            "total_additions": 12,
            "total_deletions": 3,
            "total_changes": 15,
        },
    }


def test_review_route_returns_rule_based_response(monkeypatch) -> None:
    def fake_fetch(self, owner: str, repo: str, pull_number: int) -> dict[str, object]:
        return _sample_context()

    monkeypatch.setattr(review_route.GitHubService, "fetch_pull_request_context", fake_fetch)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12", "github_token": "", "use_ai": False},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["review_mode"] == "rule_based"
    assert payload["risk_summary"]["total"] >= 1
    assert payload["markdown_report"]


def test_review_route_maps_rate_limit_error(monkeypatch) -> None:
    def fake_fetch(self, owner: str, repo: str, pull_number: int) -> dict[str, object]:
        raise GitHubAPIError("GitHub API rate limit exceeded.", status_code=429)

    monkeypatch.setattr(review_route.GitHubService, "fetch_pull_request_context", fake_fetch)
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12", "github_token": "", "use_ai": False},
    )

    assert response.status_code == 429
    assert "github_token" in response.json()["detail"].lower()


def test_review_route_falls_back_when_ai_config_is_missing(monkeypatch) -> None:
    def fake_fetch(self, owner: str, repo: str, pull_number: int) -> dict[str, object]:
        return _sample_context()

    monkeypatch.setattr(review_route.GitHubService, "fetch_pull_request_context", fake_fetch)
    monkeypatch.setattr(
        review_route,
        "get_settings",
        lambda: Settings(
            openai_api_key="",
            openai_base_url="",
            openai_model="",
            llm_temperature=0.2,
            llm_timeout=30,
            llm_max_input_chars=20000,
        ),
    )
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12", "github_token": "", "use_ai": True},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["review_mode"] == "ai_fallback"
    assert payload["ai_review"]["enabled"] is False


def test_review_route_returns_ai_assisted_response(monkeypatch) -> None:
    def fake_fetch(self, owner: str, repo: str, pull_number: int) -> dict[str, object]:
        return _sample_context()

    monkeypatch.setattr(review_route.GitHubService, "fetch_pull_request_context", fake_fetch)
    monkeypatch.setattr(review_route.LLMReviewer, "is_configured", lambda self: True)
    monkeypatch.setattr(
        review_route.LLMReviewer,
        "generate_review",
        lambda self, pr, files, risks, risk_summary, stats: {
            "enabled": True,
            "error": None,
            "pr_summary": "AI summary for review route",
            "main_changes": ["Updated review route"],
            "risk_analysis": ["Potential secret exposure"],
            "review_suggestions": ["Replace demo secret"],
            "overall_risk_level": "High",
            "confidence": "High",
        },
    )
    monkeypatch.setattr(
        review_route,
        "get_settings",
        lambda: Settings(
            openai_api_key="key",
            openai_base_url="https://api.openai.com/v1",
            openai_model="gpt-4.1-mini",
            llm_temperature=0.2,
            llm_timeout=30,
            llm_max_input_chars=20000,
        ),
    )
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12", "github_token": "", "use_ai": True},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["review_mode"] == "ai_assisted"
    assert payload["summary"] == "AI summary for review route"
