from fastapi import APIRouter

from app.models import HealthResponse, RootInfoResponse

router = APIRouter()


@router.get("/", response_model=RootInfoResponse)
def root() -> RootInfoResponse:
    return RootInfoResponse()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()
