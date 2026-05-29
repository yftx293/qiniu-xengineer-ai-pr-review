from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.routes import review as review_route
from app.services.github_service import GitHubAPIError


client = TestClient(app)


def test_parse_pr_url_endpoint_returns_parsed_payload() -> None:
    response = client.post(
        "/api/parse-pr-url",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["owner"] == "openai"
    assert payload["repo"] == "openai-python"
    assert payload["pull_number"] == 12


def test_review_route_maps_not_found_error(monkeypatch) -> None:
    def fake_fetch(self, owner: str, repo: str, pull_number: int) -> dict[str, object]:
        raise GitHubAPIError("GitHub PR not found.", status_code=404)

    monkeypatch.setattr(review_route.GitHubService, "fetch_pull_request_context", fake_fetch)

    response = client.post(
        "/api/review",
        json={"pr_url": "https://github.com/openai/openai-python/pull/12", "github_token": "", "use_ai": False},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
