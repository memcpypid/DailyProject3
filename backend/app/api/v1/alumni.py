from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.schemas.alumni import AlumniCreateRequest, AlumniImportResponse, AlumniResponse, AlumniUpdateRequest
from app.schemas.common import SuccessResponse, paginate
from app.services.alumni_service import AlumniService, to_alumni_response
from app.services.import_service import ImportError_, import_file
from app.services.import_enriched_service import import_enriched_file

router = APIRouter(prefix="/alumni", tags=["alumni"])

ALLOWED_IMPORT_EXTENSIONS = (".xlsx", ".xls", ".csv")
MAX_IMPORT_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/import-enriched", response_model=SuccessResponse[dict])
async def import_enriched_alumni(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Hanya tampilkan ringkasan, jangan simpan ke DB"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Impor file hasil scraping OSINT (DailyProject4) langsung ke profil alumni & kandidat."""
    filename = file.filename or ""
    if not filename.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file tidak didukung. Gunakan salah satu dari: {', '.join(ALLOWED_IMPORT_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ukuran file melebihi batas 25 MB")

    try:
        summary = import_enriched_file(db, current_user.id, content, filename, dry_run=dry_run)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Gagal impor: {exc}") from exc

    return SuccessResponse(
        message=f"Berhasil mengimpor {summary.candidates_created} temuan scraping!",
        data={
            "total_rows": summary.total_rows,
            "alumni_created": summary.alumni_created,
            "alumni_updated": summary.alumni_updated,
            "candidates_created": summary.candidates_created,
            "skipped_empty": summary.skipped_empty,
        }
    )


@router.post("/import", response_model=SuccessResponse[AlumniImportResponse])
async def import_alumni(
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Hanya tampilkan ringkasan, jangan simpan ke DB"),
    limit: int | None = Query(None, ge=1, description="Batasi jumlah baris yang diimpor (uji coba)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Impor data induk alumni (Nama Lulusan, NIM, Tahun Masuk, Tanggal Lulus, Fakultas,
    Program Studi) langsung dari file Excel/CSV roster kampus, ke akun yang sedang login.
    Baris dengan NIM yang sudah ada di akun ini dilewati (idempotent)."""
    filename = file.filename or ""
    if not filename.lower().endswith(ALLOWED_IMPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file tidak didukung. Gunakan salah satu dari: {', '.join(ALLOWED_IMPORT_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ukuran file melebihi batas 25 MB")

    try:
        summary = import_file(db, current_user.id, content, filename, limit=limit, dry_run=dry_run)
    except ImportError_ as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    message = (
        f"Pratinjau: {summary.created} baru, {summary.skipped_duplicate} duplikat dilewati"
        if dry_run
        else f"Impor selesai: {summary.created} alumni baru ditambahkan"
    )
    return SuccessResponse(message=message, data=AlumniImportResponse(**summary.__dict__))


@router.post("", response_model=SuccessResponse[AlumniResponse], status_code=status.HTTP_201_CREATED)
def create_alumni(
    payload: AlumniCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alumni = AlumniService(db).create(current_user.id, payload.model_dump())
    return SuccessResponse(message="Alumni berhasil ditambahkan", data=to_alumni_response(alumni))


@router.get("")
def list_alumni(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = AlumniService(db).list(current_user.id, page, limit, search, status_filter)
    return {
        "success": True,
        "message": "Daftar alumni",
        "data": {
            "alumni": [to_alumni_response(a) for a in items],
            "pagination": paginate(page, limit, total).model_dump(),
        },
    }


@router.get("/{alumni_id}", response_model=SuccessResponse[AlumniResponse])
def get_alumni(alumni_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        alumni = AlumniService(db).get_or_404(current_user.id, alumni_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SuccessResponse(message="Detail alumni", data=to_alumni_response(alumni))


@router.put("/{alumni_id}", response_model=SuccessResponse[AlumniResponse])
def update_alumni(
    alumni_id: str,
    payload: AlumniUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        alumni = AlumniService(db).update(current_user.id, alumni_id, payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SuccessResponse(message="Alumni berhasil diperbarui", data=to_alumni_response(alumni))


@router.delete("/{alumni_id}", response_model=SuccessResponse[None])
def delete_alumni(alumni_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        AlumniService(db).delete(current_user.id, alumni_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SuccessResponse(message="Alumni berhasil dihapus", data=None)
