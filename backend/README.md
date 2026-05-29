# CodeLens AI PR Review Assistant - Backend (Phase 3)

## Current Phase Capabilities
This phase extends the FastAPI backend to fetch real Pull Request context from GitHub API.

Implemented:
- `GET /` base info endpoint.
- `GET /health` health check endpoint.
- `POST /api/parse-pr-url` GitHub PR URL parser.
- `POST /api/review` fetches PR metadata and changed files from GitHub API.
- Optional `github_token` support for authenticated API requests.
- Patch truncation for each changed file (max 6000 chars).
- Basic GitHub API error handling (404, 403, 429/rate limit, timeout/network).

Not implemented in this phase:
- AI summary generation.
- Risk rule detection.
- Database persistence.
- Automatic PR comments.

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Run Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoint Tests

### 1) Health Check
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

### 2) Parse PR URL (Valid)
```bash
curl -X POST "http://127.0.0.1:8000/api/parse-pr-url" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\"}"
```

### 3) Parse PR URL (Invalid)
```bash
curl -X POST "http://127.0.0.1:8000/api/parse-pr-url" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://example.com/not-a-pr\"}"
```

### 4) Review Without Token (Public Repo)
```bash
curl -X POST "http://127.0.0.1:8000/api/review" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\",\"github_token\":\"\",\"use_ai\":false}"
```

### 5) Review With Token
```bash
curl -X POST "http://127.0.0.1:8000/api/review" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\",\"github_token\":\"<YOUR_GITHUB_TOKEN>\",\"use_ai\":false}"
```

## Notes
- Public repositories can usually be accessed without token.
- For private repositories or frequent requests, pass `github_token` to avoid permission and rate-limit issues.
- This phase keeps `use_ai` field for compatibility, but does not call any AI model yet.
- Do not commit real secrets. Create local `.env` from `.env.example` if needed.
