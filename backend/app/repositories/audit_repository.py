from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, owner_id: str, entity_type: str, entity_id: str, action: str, detail: str = "") -> AuditLog:
        entry = AuditLog(
            owner_id=owner_id, entity_type=entity_type, entity_id=entity_id, action=action, detail=detail
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_recent(self, owner_id: str, limit: int = 10) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.owner_id == owner_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
