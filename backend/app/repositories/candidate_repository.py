from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import Candidate


class CandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, alumni_id: str, source_id: str, **fields) -> Candidate:
        candidate = Candidate(alumni_id=alumni_id, source_id=source_id, **fields)
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def list_for_alumni(self, alumni_id: str) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .where(Candidate.alumni_id == alumni_id)
            .order_by(Candidate.fetched_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get(self, candidate_id: str) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)
