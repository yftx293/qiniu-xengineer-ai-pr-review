# CodeLens AI PR Review Assistant - Backend (Phase 2)

## Current Scope
This phase initializes a runnable FastAPI backend service for the CodeLens AI PR Review Assistant.

Implemented in this phase:
- `GET /` base info endpoint.
- `GET /health` health check endpoint.
- `POST /api/parse-pr-url` GitHub PR URL parsing endpoint.
- `POST /api/review` placeholder review endpoint (URL parsing only).

Not implemented yet (next phase):
- Real GitHub API diff fetching.
- LLM-based review generation.
- Frontend integration.

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Run Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test Endpoints

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

### 4) Review Placeholder
```bash
curl -X POST "http://127.0.0.1:8000/api/review" \
  -H "Content-Type: application/json" \
  -d "{\"pr_url\":\"https://github.com/owner/repo/pull/123\",\"github_token\":\"\",\"use_ai\":false}"
```

## Environment Variables
Create local `.env` yourself from `.env.example` when needed. Do not commit real secrets.
