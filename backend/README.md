# CodeLens AI PR Review Assistant - Backend (Phase 5)

## Current Phase Capabilities
This phase adds optional AI-assisted review generation and Markdown report generation.

Implemented:
- `GET /` base info endpoint.
- `GET /health` health check endpoint.
- `POST /api/parse-pr-url` GitHub PR URL parser.
- `POST /api/review` fetches PR metadata and changed files from GitHub API.
- Diff parsing and rule-based risk analysis.
- Optional AI review (`use_ai=true`) via OpenAI-compatible Chat Completions API.
- Automatic fallback to rule-based mode when AI config is missing or AI request fails.
- Markdown report generation in every review response (`markdown_report`).

Not implemented in this phase:
- Frontend UI.
- Database persistence.
- Automatic GitHub PR commenting.

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Configure Environment
Create local `.env` from `.env.example` and fill placeholders only in your local file.

```env
OPENAI_API_KEY=<YOUR_OPENAI_COMPATIBLE_API_KEY>
OPENAI_BASE_URL=<YOUR_OPENAI_COMPATIBLE_BASE_URL>
OPENAI_MODEL=<YOUR_MODEL_NAME>
LLM_TEMPERATURE=0.2
LLM_TIMEOUT=30
LLM_MAX_INPUT_CHARS=20000
```

Notes:
- `OPENAI_BASE_URL` example: `https://api.openai.com/v1` or another compatible endpoint.
- If `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` is missing, AI mode will fallback automatically.

## Run Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Test Commands

### 1) Rule Mode (`use_ai=false`)
```bash
curl -X POST "http://127.0.0.1:8000/api/review" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\",\"github_token\":\"\",\"use_ai\":false}"
```

### 2) AI-assisted Mode (`use_ai=true`)
```bash
curl -X POST "http://127.0.0.1:8000/api/review" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\",\"github_token\":\"<YOUR_GITHUB_TOKEN>\",\"use_ai\":true}"
```

### 3) Parse PR URL
```bash
curl -X POST "http://127.0.0.1:8000/api/parse-pr-url" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\"}"
```

## Review Output Notes
- `review_mode` values:
  - `rule_based`: only rules are used.
  - `ai_assisted`: AI review succeeded.
  - `ai_fallback`: AI requested but config missing or AI call failed.
- `ai_review` contains AI summary/suggestions or fallback error details.
- `markdown_report` is always returned and can be copied to GitHub PR comments.

## Risk Level & Confidence
- `severity`: impact level (`High` > `Medium` > `Low`).
- `confidence`: confidence of detection or AI inference (`High` / `Medium` / `Low`).

## Security Reminder
- Never commit `github_token`, `OPENAI_API_KEY`, or any real secret to the repository.
- Do not print or expose API keys/tokens in logs or API responses.
