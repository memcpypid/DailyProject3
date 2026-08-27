from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=SuccessResponse[DashboardStatsResponse])
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stats = DashboardService(db).stats(current_user.id)
    return SuccessResponse(message="Statistik dashboard", data=stats)
