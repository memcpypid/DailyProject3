from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni
from app.repositories.alumni_repository import AlumniRepository
from app.schemas.alumni import AlumniResponse
from app.schemas.candidate import CandidateResponse


def to_alumni_response(alumni: Alumni) -> AlumniResponse:
    try:
        variations = json.loads(alumni.name_variations or "[]")
    except (json.JSONDecodeError, TypeError):
        variations = []
    confirmed_profile = (
        CandidateResponse.from_model(alumni.confirmed_candidate) if alumni.confirmed_candidate else None
    )
    return AlumniResponse(
        id=alumni.id,
        full_name=alumni.full_name,
        nim=alumni.nim,
        tahun_masuk=alumni.tahun_masuk,
        tanggal_lulus=alumni.tanggal_lulus,
        fakultas=alumni.fakultas,
        program_studi=alumni.program_studi,
        name_variations=variations,
        status=alumni.status,
        confirmed_candidate_id=alumni.confirmed_candidate_id,
        confirmed_profile=confirmed_profile,
        last_verified_at=alumni.last_verified_at,
        created_at=alumni.created_at,
        updated_at=alumni.updated_at,
    )


class AlumniService:
    def __init__(self, db: Session):
        self.repo = AlumniRepository(db)

    def create(self, owner_id: str, payload: dict) -> Alumni:
        payload = dict(payload)
        payload["name_variations"] = json.dumps(payload.get("name_variations") or [])
        return self.repo.create(owner_id, **payload)

    def get_or_404(self, owner_id: str, alumni_id: str) -> Alumni:
        alumni = self.repo.get(owner_id, alumni_id)
        if not alumni:
            raise LookupError("Alumni tidak ditemukan")
        return alumni

    def list(self, owner_id: str, page: int, limit: int, search: str | None, status: str | None):
        return self.repo.list(owner_id, page=page, limit=limit, search=search, status=status)

    def update(self, owner_id: str, alumni_id: str, payload: dict) -> Alumni:
        alumni = self.get_or_404(owner_id, alumni_id)
        fields = {k: v for k, v in payload.items() if v is not None}
        if "name_variations" in fields:
            fields["name_variations"] = json.dumps(fields["name_variations"])
        return self.repo.update(alumni, **fields)

    def delete(self, owner_id: str, alumni_id: str) -> None:
        alumni = self.get_or_404(owner_id, alumni_id)
        self.repo.delete(alumni)
