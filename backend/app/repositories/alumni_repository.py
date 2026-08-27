from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni


class AlumniRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, owner_id: str, **fields) -> Alumni:
        alumni = Alumni(owner_id=owner_id, **fields)
        self.db.add(alumni)
        self.db.commit()
        self.db.refresh(alumni)
        return alumni

    def get(self, owner_id: str, alumni_id: str) -> Alumni | None:
        stmt = select(Alumni).where(Alumni.id == alumni_id, Alumni.owner_id == owner_id)
        return self.db.scalar(stmt)

    def list(
        self,
        owner_id: str,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Alumni], int]:
        stmt = select(Alumni).where(Alumni.owner_id == owner_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Alumni.full_name.ilike(like), Alumni.nim.ilike(like)))
        if status:
            stmt = stmt.where(Alumni.status == status)

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        stmt = stmt.order_by(Alumni.created_at.desc()).offset((page - 1) * limit).limit(limit)
        items = list(self.db.scalars(stmt))
        return items, total

    def count_by_status(self, owner_id: str) -> dict[str, int]:
        stmt = (
            select(Alumni.status, func.count())
            .where(Alumni.owner_id == owner_id)
            .group_by(Alumni.status)
        )
        return {status: count for status, count in self.db.execute(stmt)}

    def update(self, alumni: Alumni, **fields) -> Alumni:
        for key, value in fields.items():
            setattr(alumni, key, value)
        self.db.commit()
        self.db.refresh(alumni)
        return alumni

    def delete(self, alumni: Alumni) -> None:
        self.db.delete(alumni)
        self.db.commit()
