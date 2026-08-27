from datetime import datetime

from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    belum_dilacak: int
    terverifikasi_otomatis: int
    terverifikasi_manual: int
    perlu_tinjauan_manual: int
    tidak_ditemukan: int
    total: int


class ActivityItem(BaseModel):
    action: str
    entity_type: str
    detail: str
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    status_breakdown: StatusBreakdown
    source_count: int
    recent_activity: list[ActivityItem]
