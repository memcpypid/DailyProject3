from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import Source


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: str, **fields) -> Source:
        source = Source(owner_id=owner_id, **fields)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get(self, owner_id: str, source_id: str) -> Source | None:
        stmt = select(Source).where(Source.id == source_id, Source.owner_id == owner_id)
        return self.db.scalar(stmt)

    def list(self, owner_id: str) -> list[Source]:
        stmt = select(Source).where(Source.owner_id == owner_id).order_by(Source.created_at.asc())
        return list(self.db.scalars(stmt))

    def list_enabled(self, owner_id: str) -> list[Source]:
        stmt = select(Source).where(Source.owner_id == owner_id, Source.enabled.is_(True))
        return list(self.db.scalars(stmt))

    def update(self, source: Source, **fields) -> Source:
        for key, value in fields.items():
            if value is not None:
                setattr(source, key, value)
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete(self, source: Source) -> None:
        self.db.delete(source)
        self.db.commit()
