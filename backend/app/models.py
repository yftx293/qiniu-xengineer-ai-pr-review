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


class ReviewResponse(BaseModel):
    message: str
    pr: ParsedPRInfo
    use_ai: bool
