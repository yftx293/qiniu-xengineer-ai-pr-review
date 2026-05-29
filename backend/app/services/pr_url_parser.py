from __future__ import annotations

import re
from urllib.parse import urlparse

from app.models import ParsedPRInfo


class PRUrlParseError(ValueError):
    """Raised when a GitHub PR URL cannot be parsed."""


# Supports:
# - https://github.com/owner/repo/pull/123
# - http://github.com/owner/repo/pull/123
# - https://github.com/owner/repo/pull/123/files
# - https://github.com/owner/repo/pull/123?x=y
PR_PATH_PATTERN = re.compile(r"^/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)(?:/.*)?$")


def parse_github_pr_url(pr_url: str) -> ParsedPRInfo:
    raw_url = (pr_url or "").strip()
    if not raw_url:
        raise PRUrlParseError("pr_url is required and cannot be empty.")

    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise PRUrlParseError("Invalid URL scheme. Only http and https are supported.")

    host = parsed.netloc.lower()
    if host not in {"github.com", "www.github.com"}:
        raise PRUrlParseError("Invalid GitHub host. URL must point to github.com.")

    match = PR_PATH_PATTERN.match(parsed.path)
    if not match:
        raise PRUrlParseError(
            "Invalid GitHub PR URL format. Expected: https://github.com/<owner>/<repo>/pull/<number>."
        )

    owner = match.group("owner")
    repo = match.group("repo")
    pull_number = int(match.group("number"))

    html_url = f"https://github.com/{owner}/{repo}/pull/{pull_number}"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    return ParsedPRInfo(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        api_url=api_url,
        html_url=html_url,
    )
