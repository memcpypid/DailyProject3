from fastapi import APIRouter

from app.schemas.common import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[dict])
def health_check():
    return SuccessResponse(message="OK", data={"status": "healthy"})
