"""Penyimpanan temuan hasil riset manual per alumni (satu per satu, oleh manusia)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni, Candidate
from app.repositories.alumni_repository import AlumniRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.source_repository import SourceRepository


class TrackingService:
    def __init__(self, db: Session):
        self.db = db
        self.alumni_repo = AlumniRepository(db)
        self.source_repo = SourceRepository(db)
        self.candidate_repo = CandidateRepository(db)
        self.audit = AuditRepository(db)

    def add_manual_candidate(self, owner_id: str, alumni_id: str, payload: dict) -> tuple[Alumni, Candidate]:
        """Simpan temuan hasil riset manual (satu per satu, oleh manusia) untuk satu
        alumni. Temuan baru langsung menjadi data identitas terkonfirmasi alumni ini.
        """
        alumni = self.alumni_repo.get(owner_id, alumni_id)
        if not alumni:
            raise LookupError("Alumni tidak ditemukan")

        source = self.source_repo.get(owner_id, payload["source_id"])
        if not source:
            raise LookupError("Sumber data tidak ditemukan")

        fields = {k: v for k, v in payload.items() if k != "source_id"}
        candidate = self.candidate_repo.create(alumni_id=alumni.id, source_id=source.id, **fields)

        alumni = self.alumni_repo.update(
            alumni,
            status="TERVERIFIKASI_MANUAL",
            confirmed_candidate_id=candidate.id,
            last_verified_at=datetime.now(timezone.utc),
        )
        self.audit.log(
            owner_id=owner_id,
            entity_type="alumni",
            entity_id=alumni.id,
            action="manual_entry",
            detail="Input manual tersimpan, data identitas dikonfirmasi & disimpan pada profil alumni",
        )
        return alumni, candidate
