from pydantic import BaseModel, Field


class RootInfoResponse(BaseModel):
    name: str = Field(default="CodeLens AI PR Review Assistant")
    status: str = Field(default="running")
    version: str = Field(default="0.1.0")


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: str = Field(default="codelens-ai-pr-review-backend")


class ParsedPRInfo(BaseModel):
    owner: str
    repo: str
    pull_number: int
    api_url: str
    html_url: str


class ParsePRUrlRequest(BaseModel):
    pr_url: str


class ReviewRequest(BaseModel):
    pr_url: str
    github_token: str = ""
    use_ai: bool = False


class ChangedFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    raw_url: str
    blob_url: str
    patch: str
    patch_truncated: bool


class PullRequestInfo(BaseModel):
    title: str
    number: int
    state: str
    author: str
    html_url: str
    base_branch: str
    head_branch: str
    created_at: str
    updated_at: str
    additions: int
    deletions: int
    changed_files: int


class PullRequestStats(BaseModel):
    file_count: int
    total_additions: int
    total_deletions: int
    total_changes: int


class PullRequestContext(BaseModel):
    pr: PullRequestInfo
    files: list[ChangedFile]
    stats: PullRequestStats


class RiskItem(BaseModel):
    file: str | None
    line: int | None
    severity: str
    type: str
    message: str
    evidence: str | None
    suggestion: str
    confidence: str


class RiskSummary(BaseModel):
    total: int
    high: int
    medium: int
    low: int
    has_blocking_risk: bool


class AIReviewResult(BaseModel):
    enabled: bool
    error: str | None
    pr_summary: str
    main_changes: list[str]
    risk_analysis: list[str]
    review_suggestions: list[str]
    overall_risk_level: str
    confidence: str


class AnalysisTrace(BaseModel):
    rule_hits_by_type: dict[str, int]
    patch_truncated_file_count: int
    context_source: str
    ai_status: str


class ReviewResponse(BaseModel):
    message: str
    source: ParsedPRInfo
    pr: PullRequestInfo
    files: list[ChangedFile]
    stats: PullRequestStats
    summary: str
    risks: list[RiskItem]
    suggestions: list[str]
    risk_summary: RiskSummary
    ai_review: AIReviewResult | None
    analysis_trace: AnalysisTrace
    markdown_report: str
    review_mode: str
    use_ai: bool
