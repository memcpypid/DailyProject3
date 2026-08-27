from sqlalchemy.orm import Session

from app.repositories.alumni_repository import AlumniRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.source_repository import SourceRepository


class DashboardService:
    def __init__(self, db: Session):
        self.alumni_repo = AlumniRepository(db)
        self.source_repo = SourceRepository(db)
        self.audit_repo = AuditRepository(db)

    def stats(self, owner_id: str) -> dict:
        counts = self.alumni_repo.count_by_status(owner_id)
        breakdown = {
            "belum_dilacak": counts.get("BELUM_DILACAK", 0),
            "terverifikasi_manual": counts.get("TERVERIFIKASI_MANUAL", 0),
        }
        breakdown["total"] = sum(breakdown.values())

        activity = [
            {
                "action": entry.action,
                "entity_type": entry.entity_type,
                "detail": entry.detail,
                "created_at": entry.created_at,
            }
            for entry in self.audit_repo.list_recent(owner_id, limit=10)
        ]

        return {
            "status_breakdown": breakdown,
            "source_count": len(self.source_repo.list(owner_id)),
            "recent_activity": activity,
        }
