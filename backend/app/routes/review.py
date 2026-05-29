from fastapi import APIRouter, HTTPException, status

from app.models import ParsePRUrlRequest, ParsedPRInfo, ReviewRequest, ReviewResponse
from app.services.diff_parser import DiffParser
from app.services.github_service import GitHubAPIError, GitHubService
from app.services.pr_url_parser import PRUrlParseError, parse_github_pr_url
from app.services.risk_analyzer import RiskAnalyzer

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/parse-pr-url", response_model=ParsedPRInfo)
def parse_pr_url(payload: ParsePRUrlRequest) -> ParsedPRInfo:
    try:
        return parse_github_pr_url(payload.pr_url)
    except PRUrlParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/review", response_model=ReviewResponse)
def review_pr(payload: ReviewRequest) -> ReviewResponse:
    try:
        source = parse_github_pr_url(payload.pr_url)
    except PRUrlParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    service = GitHubService(token=payload.github_token)
    try:
        context = service.fetch_pull_request_context(source.owner, source.repo, source.pull_number)
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub PR not found. Please verify the PR URL.") from exc
        if exc.status_code in {429, 403} and "rate limit" in str(exc).lower():
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please provide github_token and retry.",
            ) from exc
        if exc.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="GitHub API access denied. The repository may be private or token is missing/invalid.",
            ) from exc
        if exc.status_code == 502:
            raise HTTPException(status_code=502, detail="Failed to connect to GitHub API.") from exc
        raise HTTPException(status_code=500, detail="GitHub API request failed unexpectedly.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error.") from exc

    parsed_diffs = DiffParser.parse_files(context["files"])
    risk_result = RiskAnalyzer().analyze_files(context["files"], parsed_diffs)
    risk_summary = risk_result["risk_summary"]

    message = "Fetched PR metadata and changed files successfully. Rule-based risk analysis completed."
    if payload.use_ai:
        message = (
            f"{message} AI review is not implemented in this stage, using rule-based analysis only."
        )

    summary = (
        "Rule-based risk analysis found "
        f"{risk_summary['total']} risks, including {risk_summary['high']} high risk items."
    )

    return ReviewResponse(
        message=message,
        source=source,
        pr=context["pr"],
        files=context["files"],
        stats=context["stats"],
        summary=summary,
        risks=risk_result["risks"],
        suggestions=risk_result["suggestions"],
        risk_summary=risk_summary,
        use_ai=payload.use_ai,
    )
