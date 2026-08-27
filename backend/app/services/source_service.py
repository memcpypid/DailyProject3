from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.models import Source
from app.repositories.source_repository import SourceRepository

# Registrasi Sumber Data & Bobot Kepercayaan (langkah 2 pseudocode) - sumber default per akun baru.
# Daftar sesuai Daily Project 4: 4 platform sosial media eksplisit + situs
# perusahaan/berita (untuk data pekerjaan) + mesin pencari umum sebagai fallback.
DEFAULT_SOURCES = [
    {"name": "LinkedIn", "access_type": "API/partner bila tersedia, fallback pencarian web sesuai ToS", "weight": 0.9},
    {"name": "Instagram", "access_type": "Pencarian nama publik terbatas, tanpa login", "weight": 0.6},
    {"name": "Facebook", "access_type": "Pencarian nama publik terbatas, tanpa login", "weight": 0.6},
    {"name": "TikTok", "access_type": "Pencarian nama publik terbatas, tanpa login", "weight": 0.4},
    {"name": "Situs Perusahaan / Berita", "access_type": "Directory staf, berita, press release", "weight": 0.7},
    {"name": "Mesin Pencari Umum", "access_type": "Fallback pencarian web umum", "weight": 0.4},
]


class SourceService:
    def __init__(self, db: Session):
        self.repo = SourceRepository(db)

    def seed_defaults(self, owner_id: str) -> list[Source]:
        return [self.repo.create(owner_id, **item) for item in DEFAULT_SOURCES]

    def list(self, owner_id: str) -> list[Source]:
        return self.repo.list(owner_id)

    def create(self, owner_id: str, **fields) -> Source:
        return self.repo.create(owner_id, **fields)

    def get_or_404(self, owner_id: str, source_id: str) -> Source:
        source = self.repo.get(owner_id, source_id)
        if not source:
            raise LookupError("Sumber data tidak ditemukan")
        return source

    def update(self, owner_id: str, source_id: str, **fields) -> Source:
        source = self.get_or_404(owner_id, source_id)
        return self.repo.update(source, **fields)

    def delete(self, owner_id: str, source_id: str) -> None:
        source = self.get_or_404(owner_id, source_id)
        self.repo.delete(source)
