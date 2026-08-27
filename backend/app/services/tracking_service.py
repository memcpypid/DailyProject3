"""Penyimpanan temuan hasil riset manual per alumni (satu per satu, oleh manusia)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni, Candidate
from app.repositories.alumni_repository import AlumniRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.source_repository import SourceRepository
from app.services.scoring_service import score_candidate


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
        scores = score_candidate(alumni, fields, source.weight)
        fields.update(scores)
        candidate = self.candidate_repo.create(alumni_id=alumni.id, source_id=source.id, **fields)
        identity_fields = ("email", "phone", "linkedin_url", "instagram_url", "facebook_url", "tiktok_url")
        related_sources = {candidate.source_id}
        for other in self.candidate_repo.list_for_alumni(alumni.id):
            if other.id == candidate.id or other.source_id == candidate.source_id:
                continue
            same_name = bool(candidate.raw_name and other.raw_name and candidate.raw_name.casefold() == other.raw_name.casefold())
            same_identity = any(
                getattr(candidate, key) and getattr(candidate, key) == getattr(other, key)
                for key in identity_fields
            )
            if same_name or same_identity:
                related_sources.add(other.source_id)
        candidate.evidence_count = len(related_sources)
        candidate.match_score = min(100.0, candidate.match_score + max(0, candidate.evidence_count - 1) * 5)
        self.db.commit()
        self.db.refresh(candidate)
        if candidate.match_score >= 80:
            next_status = "TERVERIFIKASI_OTOMATIS"
            confirmed_id = candidate.id
        elif candidate.match_score >= 50:
            next_status = "PERLU_TINJAUAN_MANUAL"
            confirmed_id = alumni.confirmed_candidate_id
        else:
            next_status = "TIDAK_DITEMUKAN"
            confirmed_id = alumni.confirmed_candidate_id
        alumni = self.alumni_repo.update(alumni, status=next_status, confirmed_candidate_id=confirmed_id)
        self.audit.log(
            owner_id=owner_id,
            entity_type="alumni",
            entity_id=alumni.id,
            action="manual_entry",
            detail=f"Kandidat dinilai {candidate.match_score:.2f}; status menjadi {next_status}",
        )
        return alumni, candidate

    def review_candidate(self, owner_id: str, alumni_id: str, candidate_id: str, decision: str) -> tuple[Alumni, Candidate]:
        alumni = self.alumni_repo.get(owner_id, alumni_id)
        candidate = self.candidate_repo.get(candidate_id)
        if not alumni or not candidate or candidate.alumni_id != alumni.id:
            raise LookupError("Kandidat tidak ditemukan")
        decision = decision.upper()
        mapping = {
            "ACCEPT": ("ACCEPTED", "TERVERIFIKASI_MANUAL", candidate.id),
            "REJECT": ("REJECTED", "TIDAK_DITEMUKAN", None),
            "RECHECK": ("RECHECK", "PERLU_TINJAUAN_MANUAL", alumni.confirmed_candidate_id),
        }
        if decision not in mapping:
            raise ValueError("Keputusan harus ACCEPT, REJECT, atau RECHECK")
        review_status, alumni_status, confirmed_id = mapping[decision]
        candidate.review_status = review_status
        candidate.reviewed_at = datetime.now(timezone.utc)
        alumni.status = alumni_status
        alumni.confirmed_candidate_id = confirmed_id
        if decision == "ACCEPT":
            alumni.last_verified_at = candidate.reviewed_at
        self.db.commit()
        self.db.refresh(candidate)
        self.db.refresh(alumni)
        self.audit.log(owner_id=owner_id, entity_type="alumni", entity_id=alumni.id,
                       action=f"review_{decision.lower()}", detail=f"Kandidat {candidate.id} diputuskan {decision}")
        return alumni, candidate
