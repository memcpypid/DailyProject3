from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def migrate_sqlite_schema() -> None:
    """Migrasi aditif kecil agar database proyek lama tetap dapat digunakan."""
    if engine.dialect.name != "sqlite" or "candidates" not in inspect(engine).get_table_names():
        return
    existing = {column["name"] for column in inspect(engine).get_columns("candidates")}
    additions = {
        "name_score": "FLOAT NOT NULL DEFAULT 0",
        "affiliation_score": "FLOAT NOT NULL DEFAULT 0",
        "timeline_score": "FLOAT NOT NULL DEFAULT 0",
        "field_score": "FLOAT NOT NULL DEFAULT 0",
        "match_score": "FLOAT NOT NULL DEFAULT 0",
        "evidence_count": "INTEGER NOT NULL DEFAULT 1",
        "review_status": "VARCHAR(24) NOT NULL DEFAULT 'PENDING'",
        "reviewed_at": "DATETIME",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE candidates ADD COLUMN {name} {definition}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
