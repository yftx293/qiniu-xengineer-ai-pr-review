from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.review import router as review_router


app = FastAPI(
    title="CodeLens AI PR Review Assistant Backend",
    version="0.2.0",
    description="Backend service for PR URL parsing and GitHub PR context fetching.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(review_router)
