from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
PATCH_MAX_LENGTH = 6000
MAX_FILE_PAGES = 5
PER_PAGE = 100


@dataclass
class GitHubAPIError(Exception):
    message: str
    status_code: int = 500

    def __str__(self) -> str:
        return self.message


class GitHubService:
    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        cleaned = (token or "").strip()
        self.token = cleaned if cleaned else None
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{GITHUB_API_BASE_URL}{path}"
        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=self.timeout)
        except requests.exceptions.Timeout as exc:
            raise GitHubAPIError("Failed to connect to GitHub API: request timed out.", status_code=502) from exc
        except requests.exceptions.ConnectionError as exc:
            raise GitHubAPIError("Failed to connect to GitHub API: network error.", status_code=502) from exc
        except requests.exceptions.RequestException as exc:
            raise GitHubAPIError("Failed to connect to GitHub API.", status_code=502) from exc

        if 200 <= response.status_code < 300:
            return response.json()

        self._raise_for_error(response)
        return None

    def _raise_for_error(self, response: requests.Response) -> None:
        status_code = response.status_code
        try:
            payload = response.json()
            remote_message = payload.get("message", "") if isinstance(payload, dict) else ""
        except ValueError:
            remote_message = ""

        if status_code == 404:
            raise GitHubAPIError("GitHub PR not found. Please check owner, repo, and pull number.", status_code=404)

        if status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubAPIError(
                "GitHub API rate limit exceeded. Please provide a github_token and try again.",
                status_code=429,
            )

        if status_code == 403:
            raise GitHubAPIError(
                "GitHub API request forbidden. The repository may be private or access is denied.",
                status_code=403,
            )

        message = f"GitHub API request failed with status {status_code}."
        if remote_message:
            message = f"{message} Details: {remote_message}"
        raise GitHubAPIError(message, status_code=status_code)

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> dict[str, Any]:
        return self._request(f"/repos/{owner}/{repo}/pulls/{pull_number}")

    def list_pull_request_files(self, owner: str, repo: str, pull_number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []

        for page in range(1, MAX_FILE_PAGES + 1):
            page_items = self._request(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
                params={"per_page": PER_PAGE, "page": page},
            )

            if not isinstance(page_items, list):
                raise GitHubAPIError("Unexpected GitHub API response format for pull request files.", status_code=502)

            if not page_items:
                break

            files.extend(page_items)
            if len(page_items) < PER_PAGE:
                break

        return files

    def fetch_pull_request_context(self, owner: str, repo: str, pull_number: int) -> dict[str, Any]:
        pr_data = self.get_pull_request(owner, repo, pull_number)
        file_data = self.list_pull_request_files(owner, repo, pull_number)

        files: list[dict[str, Any]] = []
        total_additions = 0
        total_deletions = 0

        for item in file_data:
            patch = item.get("patch") or ""
            patch_truncated = len(patch) > PATCH_MAX_LENGTH
            if patch_truncated:
                patch = patch[:PATCH_MAX_LENGTH]

            additions = int(item.get("additions", 0) or 0)
            deletions = int(item.get("deletions", 0) or 0)
            changes = int(item.get("changes", additions + deletions) or 0)

            total_additions += additions
            total_deletions += deletions

            files.append(
                {
                    "filename": item.get("filename", ""),
                    "status": item.get("status", "unknown"),
                    "additions": additions,
                    "deletions": deletions,
                    "changes": changes,
                    "raw_url": item.get("raw_url", ""),
                    "blob_url": item.get("blob_url", ""),
                    "patch": patch,
                    "patch_truncated": patch_truncated,
                }
            )

        stats = {
            "file_count": len(files),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_additions + total_deletions,
        }

        pr = {
            "title": pr_data.get("title", ""),
            "number": int(pr_data.get("number", pull_number)),
            "state": pr_data.get("state", "unknown"),
            "author": (pr_data.get("user") or {}).get("login", "unknown"),
            "html_url": pr_data.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pull_number}"),
            "base_branch": (pr_data.get("base") or {}).get("ref", ""),
            "head_branch": (pr_data.get("head") or {}).get("ref", ""),
            "created_at": pr_data.get("created_at", ""),
            "updated_at": pr_data.get("updated_at", ""),
            "additions": int(pr_data.get("additions", stats["total_additions"])),
            "deletions": int(pr_data.get("deletions", stats["total_deletions"])),
            "changed_files": int(pr_data.get("changed_files", stats["file_count"])),
        }

        return {
            "pr": pr,
            "files": files,
            "stats": stats,
        }
