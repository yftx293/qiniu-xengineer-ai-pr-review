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


def _build_rule_summary(risk_summary: dict[str, int], rule_hits_by_type: dict[str, int]) -> str:
    total = int(risk_summary.get("total", 0) or 0)
    high = int(risk_summary.get("high", 0) or 0)
    medium = int(risk_summary.get("medium", 0) or 0)

    if total == 0:
        return "规则审查未发现明显高风险信号，但仍建议结合业务上下文确认关键路径、异常处理和回归覆盖是否完整。"

    top_types = sorted(rule_hits_by_type.items(), key=lambda item: (-item[1], item[0]))[:2]
    top_type_text = "、".join(risk_type for risk_type, _count in top_types)

    if high > 0:
        return (
            f"规则审查共识别 {total} 项风险提示，其中 High 风险 {high} 项、Medium 风险 {medium} 项。"
            f"当前最值得优先复核的方向是：{top_type_text or '高风险代码路径'}。"
        )

    return (
        f"规则审查共识别 {total} 项中低风险提示，主要集中在 {top_type_text or '变更影响面'}。"
        "建议结合具体业务场景确认这些提示是否会在真实运行路径中放大。"
    )


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

    rule_summary = _build_rule_summary(risk_summary, rule_result["rule_hits_by_type"])
    message = "Fetched PR metadata and changed files successfully. Rule-based risk analysis completed."
    review_mode = "rule_based"
    ai_status = "not_requested"
    fallback_reason = None
    ai_review = None
    ai_context_file_count = 0
    top_risk_file_count = len({risk.get("file") for risk in rule_result["risks"] if risk.get("file") and risk.get("severity") in {"High", "Medium"}})

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
        ai_context_file_count = int(llm_reviewer.last_prompt_metadata.get("ai_context_file_count", 0) or 0)
        top_risk_file_count = int(llm_reviewer.last_prompt_metadata.get("top_risk_file_count", top_risk_file_count) or 0)

        if ai_configured and ai_review.get("enabled"):
            review_mode = "ai_assisted"
            ai_status = "completed"
            message = "Fetched PR metadata and changed files successfully. AI-assisted review completed."
        elif not ai_configured:
            review_mode = "ai_fallback"
            ai_status = "config_missing"
            fallback_reason = "ai_config_missing"
            message = (
                "Fetched PR metadata and changed files successfully. "
                "AI config is missing, fallback to rule-based review."
            )
        else:
            review_mode = "ai_fallback"
            ai_status = "fallback_error"
            fallback_reason = "ai_generation_failed"
            message = (
                "Fetched PR metadata and changed files successfully. "
                "AI review failed, fallback to rule-based review."
            )

    analysis_trace = {
        "rule_hits_by_type": rule_result["rule_hits_by_type"],
        "patch_truncated_file_count": sum(1 for file_item in context["files"] if file_item.get("patch_truncated")),
        "context_source": "github_api_pr_and_files",
        "ai_status": ai_status,
        "fallback_reason": fallback_reason,
        "top_risk_file_count": top_risk_file_count,
        "ai_context_file_count": ai_context_file_count,
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
