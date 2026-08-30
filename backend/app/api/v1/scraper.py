from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.infrastructure.models import User
from app.schemas.common import SuccessResponse
from app.services.scraper_service import scraper_manager

router = APIRouter(prefix="/scraper", tags=["scraper"])


class StartScraperRequest(BaseModel):
    workers: int = Field(10, ge=1, le=20, description="Jumlah worker paralel")
    limit: Optional[int] = Field(50, ge=0, description="Batas jumlah alumni yang diproses (0 untuk semua)")
    status_filter: Optional[str] = Field("BELUM_DILACAK", description="Filter status alumni (default: BELUM_DILACAK)")
    univ_keyword: str = Field("", description="Keyword tambahan institusi/kampus")
    delay_min: float = Field(0.8, ge=0.2, description="Delay minimum per request")
    delay_max: float = Field(2.0, ge=0.5, description="Delay maksimum per request")


@router.post("/start", response_model=SuccessResponse[Dict[str, Any]])
def start_scraper(
    payload: StartScraperRequest,
    current_user: User = Depends(get_current_user),
):
    """Mulai proses background scraping OSINT otomatis."""
    started = scraper_manager.start(
        owner_id=current_user.id,
        workers=payload.workers,
        limit=payload.limit if payload.limit > 0 else None,
        status_filter=payload.status_filter if payload.status_filter != "ALL" else None,
        univ_keyword=payload.univ_keyword,
        delay_min=payload.delay_min,
        delay_max=payload.delay_max,
    )
    if not started:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scraper saat ini sudah berjalan. Hentikan terlebih dahulu sebelum memulai sesi baru.",
        )
    return SuccessResponse(
        message=f"Auto-Scraping OSINT Bot berhasil dimulai dengan {payload.workers} Worker!",
        data=scraper_manager.get_status(),
    )


@router.post("/stop", response_model=SuccessResponse[Dict[str, Any]])
def stop_scraper(current_user: User = Depends(get_current_user)):
    """Hentikan proses background scraping."""
    scraper_manager.stop()
    return SuccessResponse(
        message="Perintah penghentian scraper telah dikirim.",
        data=scraper_manager.get_status(),
    )


@router.get("/status", response_model=SuccessResponse[Dict[str, Any]])
def get_scraper_status(current_user: User = Depends(get_current_user)):
    """Ambil status terbaru sesi scraping (progress, count, worker)."""
    return SuccessResponse(message="Status scraper", data=scraper_manager.get_status())


@router.get("/logs", response_model=SuccessResponse[List[Dict[str, Any]]])
def get_scraper_logs(
    limit: int = Query(50, ge=5, le=200),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar log aktivitas temuan data scraping real-time."""
    return SuccessResponse(
        message="Log aktivitas scraper",
        data=scraper_manager.get_logs(limit=limit),
    )
