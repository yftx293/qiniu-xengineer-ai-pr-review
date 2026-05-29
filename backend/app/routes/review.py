from fastapi import APIRouter, HTTPException, status

from app.models import ParsePRUrlRequest, ParsedPRInfo, ReviewRequest, ReviewResponse
from app.services.pr_url_parser import PRUrlParseError, parse_github_pr_url

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
        pr_info = parse_github_pr_url(payload.pr_url)
    except PRUrlParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ReviewResponse(
        message="PR URL parsed successfully. GitHub diff fetching will be implemented in the next stage.",
        pr=pr_info,
        use_ai=payload.use_ai,
    )
