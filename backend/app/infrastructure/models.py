import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    alumni: Mapped[list["Alumni"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    sources: Mapped[list["Source"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    access_type: Mapped[str] = mapped_column(String(255), default="")
    weight: Mapped[float] = mapped_column(Float, default=0.5)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="sources")


class Alumni(Base):
    """Data induk alumni - kolomnya mengikuti roster resmi dari kampus:
    Nama Lulusan, NIM, Tahun Masuk, Tanggal Lulus, Fakultas, Program Studi.
    """

    __tablename__ = "alumni"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    full_name: Mapped[str] = mapped_column(String(160), nullable=False)  # Nama Lulusan
    nim: Mapped[str] = mapped_column(String(40), default="", index=True)
    tahun_masuk: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tanggal_lulus: Mapped[date | None] = mapped_column(Date, nullable=True)
    fakultas: Mapped[str] = mapped_column(String(160), default="")
    program_studi: Mapped[str] = mapped_column(String(160), default="")
    name_variations: Mapped[str] = mapped_column(Text, default="[]")  # JSON-encoded list[str]

    status: Mapped[str] = mapped_column(String(32), default="BELUM_DILACAK")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Kandidat yang disimpan manusia (hasil riset manual per alumni, satu per satu)
    # sebagai data identitas final alumni ini - lihat TrackingService.add_manual_candidate.
    # NULL berarti belum ada temuan yang tersimpan.
    confirmed_candidate_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="alumni")
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="alumni", cascade="all, delete-orphan", foreign_keys="Candidate.alumni_id"
    )
    confirmed_candidate: Mapped["Candidate | None"] = relationship(
        foreign_keys=[confirmed_candidate_id], post_update=True
    )


class Candidate(Base):
    """Satu temuan data alumni dari satu sumber, mencakup 8 data target:
    sosial media (LinkedIn/IG/FB/TikTok), email, no HP, tempat & alamat kerja,
    posisi, jenis pekerjaan (PNS/Swasta/Wirausaha), dan sosial media tempat kerja.
    """

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    alumni_id: Mapped[str] = mapped_column(String(32), ForeignKey("alumni.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(32), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)

    raw_name: Mapped[str] = mapped_column(String(160), default="")

    # 1. Alamat sosial media
    linkedin_url: Mapped[str] = mapped_column(String(255), default="")
    instagram_url: Mapped[str] = mapped_column(String(255), default="")
    facebook_url: Mapped[str] = mapped_column(String(255), default="")
    tiktok_url: Mapped[str] = mapped_column(String(255), default="")
    # 2-3. Kontak
    email: Mapped[str] = mapped_column(String(160), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    # 4-7. Pekerjaan
    employer_name: Mapped[str] = mapped_column(String(200), default="")
    employer_address: Mapped[str] = mapped_column(String(255), default="")
    position: Mapped[str] = mapped_column(String(160), default="")
    employment_type: Mapped[str] = mapped_column(String(20), default="")  # PNS | Swasta | Wirausaha
    # 8. Sosial media tempat bekerja
    employer_social_media: Mapped[str] = mapped_column(String(255), default="")

    snippet: Mapped[str] = mapped_column(Text, default="")

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    alumni: Mapped["Alumni"] = relationship(back_populates="candidates", foreign_keys=[alumni_id])
    source: Mapped["Source"] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
