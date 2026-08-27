"""Impor data induk alumni dari file Excel/CSV roster kampus (dipakai bersama oleh
endpoint API `POST /api/v1/alumni/import` dan skrip CLI `scripts/import_alumni.py`).

Kolom sumber yang diharapkan (persis seperti file dari kampus):
    Nama Lulusan | NIM | Tahun Masuk | Tanggal Lulus | Fakultas | Program Studi

Data ini adalah data induk (roster), BUKAN hasil pencarian/scraping - jadi aman
untuk diimpor apa adanya. Data pribadi (sosial media/email/dst.) TIDAK pernah
dikumpulkan otomatis untuk hasil impor ini - hanya lewat riset manual satu
alumni pada satu waktu (lihat app/services/tracking_service.py).
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni

COLUMN_MAP = {
    "Nama Lulusan": "full_name",
    "NIM": "nim",
    "Tahun Masuk": "tahun_masuk",
    "Tanggal Lulus": "tanggal_lulus",
    "Fakultas": "fakultas",
    "Program Studi": "program_studi",
}

INDO_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
}

MAX_ROW_ERRORS_KEPT = 20


class ImportError_(Exception):
    """Kesalahan yang menghentikan seluruh proses impor (mis. kolom hilang)."""


@dataclass
class ImportSummary:
    total_rows: int = 0
    created: int = 0
    skipped_duplicate: int = 0
    skipped_duplicate_in_file: int = 0
    skipped_duplicate_in_db: int = 0
    skipped_invalid: int = 0
    errors: list[str] = field(default_factory=list)


def parse_tanggal(value):
    """Parse tanggal berformat "1 Juli 2000" tanpa bergantung pada locale sistem
    (nama bulan strptime %B bersifat locale-dependent, jadi dihindari di sini)."""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()

    parts = str(value).strip().lower().split()
    if len(parts) == 3 and parts[1] in INDO_MONTHS:
        day, month_name, year = parts
        try:
            return datetime(int(year), INDO_MONTHS[month_name], int(day)).date()
        except ValueError:
            return None

    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _read_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    buffer = io.BytesIO(content)
    lower = filename.lower()
    if lower.endswith(".csv"):
        return pd.read_csv(buffer)
    return pd.read_excel(buffer)  # .xlsx / .xls


def import_dataframe(
    db: Session, owner_id: str, df: pd.DataFrame, *, limit: int | None = None, dry_run: bool = False
) -> ImportSummary:
    missing = set(COLUMN_MAP) - set(df.columns)
    if missing:
        raise ImportError_(f"Kolom berikut tidak ditemukan di file: {', '.join(sorted(missing))}")

    if limit:
        df = df.head(limit)

    summary = ImportSummary(total_rows=len(df))

    existing_nims_db = {
        row.nim for row in db.query(Alumni.nim).filter(Alumni.owner_id == owner_id) if row.nim
    }
    existing_nims = set(existing_nims_db)
    first_seen_row: dict[str, int] = {}

    to_create: list[Alumni] = []
    for idx, row in df.iterrows():
        excel_row = idx + 2  # +1 untuk header, +1 karena iterrows 0-based

        full_name = str(row["Nama Lulusan"]).strip() if pd.notna(row["Nama Lulusan"]) else ""
        nim = str(row["NIM"]).strip() if pd.notna(row["NIM"]) else ""

        if not full_name or not nim:
            summary.skipped_invalid += 1
            if len(summary.errors) < MAX_ROW_ERRORS_KEPT:
                summary.errors.append(f"Baris {excel_row}: Nama Lulusan/NIM kosong, dilewati")
            continue

        if nim in existing_nims:
            summary.skipped_duplicate += 1
            if nim in existing_nims_db:
                summary.skipped_duplicate_in_db += 1
                reason = "NIM sudah tersimpan di database"
            else:
                summary.skipped_duplicate_in_file += 1
                reason = f"NIM duplikat di file, sudah dipakai baris {first_seen_row[nim]}"
            if len(summary.errors) < MAX_ROW_ERRORS_KEPT:
                summary.errors.append(f"Baris {excel_row}: NIM {nim} dilewati - {reason}")
            continue
        existing_nims.add(nim)
        first_seen_row[nim] = excel_row

        to_create.append(
            Alumni(
                owner_id=owner_id,
                full_name=full_name,
                nim=nim,
                tahun_masuk=int(row["Tahun Masuk"]) if pd.notna(row["Tahun Masuk"]) else None,
                tanggal_lulus=parse_tanggal(row["Tanggal Lulus"]),
                fakultas=str(row["Fakultas"]).strip() if pd.notna(row["Fakultas"]) else "",
                program_studi=str(row["Program Studi"]).strip() if pd.notna(row["Program Studi"]) else "",
                name_variations=json.dumps([]),
                status="BELUM_DILACAK",
            )
        )

    summary.created = len(to_create)

    if not dry_run and to_create:
        db.bulk_save_objects(to_create)
        db.commit()

    return summary


def import_file(
    db: Session, owner_id: str, content: bytes, filename: str, *, limit: int | None = None, dry_run: bool = False
) -> ImportSummary:
    try:
        df = _read_dataframe(content, filename)
    except Exception as exc:  # noqa: BLE001 - file sungguhan bisa gagal dengan berbagai cara
        raise ImportError_(f"Gagal membaca file: {exc}") from exc
    return import_dataframe(db, owner_id, df, limit=limit, dry_run=dry_run)
