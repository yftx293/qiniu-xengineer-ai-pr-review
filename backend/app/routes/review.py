from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.models import ParsePRUrlRequest, ParsedPRInfo, ReviewRequest, ReviewResponse
from app.services.diff_parser import DiffParser
from app.services.github_service import GitHubAPIError, GitHubService
from app.services.llm_reviewer import LLMReviewer
from app.services.pr_url_parser import PRUrlParseError, parse_github_pr_url
from app.services.report_service import ReportService
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

    github_service = GitHubService(token=payload.github_token)
    try:
        context = github_service.fetch_pull_request_context(source.owner, source.repo, source.pull_number)
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
    rule_result = RiskAnalyzer().analyze_files(context["files"], parsed_diffs)
    risk_summary = rule_result["risk_summary"]

    rule_summary = (
        "Rule-based risk analysis found "
        f"{risk_summary['total']} risks, including {risk_summary['high']} high risk items."
    )
    message = "Fetched PR metadata and changed files successfully. Rule-based risk analysis completed."
    review_mode = "rule_based"
    ai_status = "not_requested"
    ai_review = None

    if payload.use_ai:
        settings = get_settings()
        llm_reviewer = LLMReviewer(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
            max_input_chars=settings.llm_max_input_chars,
        )
        ai_configured = llm_reviewer.is_configured()
        ai_review = llm_reviewer.generate_review(
            pr=context["pr"],
            files=context["files"],
            risks=rule_result["risks"],
            risk_summary=rule_result["risk_summary"],
            stats=context["stats"],
        )

        if ai_configured and ai_review.get("enabled"):
            review_mode = "ai_assisted"
            ai_status = "completed"
            message = "Fetched PR metadata and changed files successfully. AI-assisted review completed."
        elif not ai_configured:
            review_mode = "ai_fallback"
            ai_status = "config_missing"
            message = (
                "Fetched PR metadata and changed files successfully. "
                "AI config is missing, fallback to rule-based review."
            )
        else:
            review_mode = "ai_fallback"
            ai_status = "fallback_error"
            message = (
                "Fetched PR metadata and changed files successfully. "
                "AI review failed, fallback to rule-based review."
            )

    analysis_trace = {
        "rule_hits_by_type": rule_result["rule_hits_by_type"],
        "patch_truncated_file_count": sum(1 for file_item in context["files"] if file_item.get("patch_truncated")),
        "context_source": "github_api_pr_and_files",
        "ai_status": ai_status,
    }

    summary = rule_summary
    if ai_review and ai_review.get("enabled") and ai_review.get("pr_summary"):
        summary = ai_review.get("pr_summary", rule_summary)

    markdown_report = ReportService().build_markdown_report(
        pr=context["pr"],
        stats=context["stats"],
        files=context["files"],
        summary=summary,
        risks=rule_result["risks"],
        suggestions=rule_result["suggestions"],
        risk_summary=rule_result["risk_summary"],
        analysis_trace=analysis_trace,
        ai_review=ai_review,
    )

    return ReviewResponse(
        message=message,
        source=source,
        pr=context["pr"],
        files=context["files"],
        stats=context["stats"],
        summary=summary,
        risks=rule_result["risks"],
        suggestions=rule_result["suggestions"],
        risk_summary=rule_result["risk_summary"],
        ai_review=ai_review,
        analysis_trace=analysis_trace,
        markdown_report=markdown_report,
        review_mode=review_mode,
        use_ai=payload.use_ai,
    )
