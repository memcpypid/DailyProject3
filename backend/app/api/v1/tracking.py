from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import CandidateResponse, ManualCandidateRequest
from app.schemas.common import SuccessResponse
from app.schemas.websearch import WebSearchResult
from app.services import websearch_service
from app.services.tracking_service import TrackingService

router = APIRouter(tags=["tracking"])


@router.post("/alumni/{alumni_id}/candidates/manual", response_model=SuccessResponse[CandidateResponse],
             status_code=status.HTTP_201_CREATED)
def add_manual_candidate(
    alumni_id: str,
    payload: ManualCandidateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simpan temuan yang benar-benar sudah diverifikasi manual oleh periset,
    satu alumni pada satu waktu (tidak ada pengumpulan data otomatis-massal)."""
    try:
        _, candidate = TrackingService(db).add_manual_candidate(current_user.id, alumni_id, payload.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SuccessResponse(message="Temuan manual tersimpan", data=CandidateResponse.from_model(candidate))


@router.get("/alumni/{alumni_id}/candidates", response_model=SuccessResponse[list[CandidateResponse]])
def list_candidates(alumni_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.alumni_service import AlumniService

    try:
        AlumniService(db).get_or_404(current_user.id, alumni_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    candidates = CandidateRepository(db).list_for_alumni(alumni_id)
    return SuccessResponse(
        message="Daftar kandidat",
        data=[CandidateResponse.from_model(c) for c in candidates],
    )


@router.get("/alumni/{alumni_id}/search-web", response_model=SuccessResponse[list[WebSearchResult]])
def search_web(alumni_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Pencarian web sungguhan untuk SATU alumni, dipicu manual oleh periset.

    Hasil hanya ditampilkan - tidak ada yang tersimpan ke database di sini.
    Periset meninjau hasilnya sendiri lalu menyimpan data yang benar lewat
    POST /alumni/{id}/candidates/manual - sengaja tidak dijalankan otomatis
    untuk banyak alumni sekaligus.
    """
    from app.repositories.audit_repository import AuditRepository
    from app.repositories.source_repository import SourceRepository
    from app.services.alumni_service import AlumniService

    try:
        alumni = AlumniService(db).get_or_404(current_user.id, alumni_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    sources = SourceRepository(db).list_enabled(current_user.id)
    try:
        results = websearch_service.search_alumni(
            {
                "full_name": alumni.full_name,
                "nim": alumni.nim,
                "tahun_masuk": alumni.tahun_masuk,
                "tanggal_lulus": alumni.tanggal_lulus.isoformat() if alumni.tanggal_lulus else "",
                "fakultas": alumni.fakultas,
                "program_studi": alumni.program_studi,
            },
            sources,
        )
    except websearch_service.WebSearchUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    AuditRepository(db).log(
        owner_id=current_user.id,
        entity_type="alumni",
        entity_id=alumni.id,
        action="search_web",
        detail=f"Pencarian web manual dilakukan ({len(results)} hasil ditampilkan, belum tersimpan)",
    )
    return SuccessResponse(message="Hasil pencarian web", data=results)
