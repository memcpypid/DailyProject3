from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.schemas.common import SuccessResponse
from app.schemas.source import SourceCreateRequest, SourceResponse, SourceUpdateRequest
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=SuccessResponse[list[SourceResponse]])
def list_sources(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sources = SourceService(db).list(current_user.id)
    return SuccessResponse(message="Daftar sumber data", data=[SourceResponse.model_validate(s) for s in sources])


@router.post("", response_model=SuccessResponse[SourceResponse], status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source = SourceService(db).create(current_user.id, **payload.model_dump())
    return SuccessResponse(message="Sumber data berhasil ditambahkan", data=SourceResponse.model_validate(source))


@router.put("/{source_id}", response_model=SuccessResponse[SourceResponse])
def update_source(
    source_id: str,
    payload: SourceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        source = SourceService(db).update(current_user.id, source_id, **payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SuccessResponse(message="Sumber data berhasil diperbarui", data=SourceResponse.model_validate(source))


@router.delete("/{source_id}", response_model=SuccessResponse[None])
def delete_source(source_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        SourceService(db).delete(current_user.id, source_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SuccessResponse(message="Sumber data berhasil dihapus", data=None)
