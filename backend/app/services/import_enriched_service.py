"""
Layanan Impor Data Hasil Scraping / Enrichment (DailyProject4 -> DailyProject3)
Membaca file CSV/Excel hasil scraping dan menyimpan temuan 8 data target
ke dalam tabel alumni & candidates sebagai profil terverifikasi.
"""

from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.infrastructure.models import Alumni, Candidate, Source, User, _now, _uuid
from app.services.import_service import parse_tanggal


@dataclass
class EnrichedImportSummary:
    total_rows: int = 0
    alumni_created: int = 0
    alumni_updated: int = 0
    candidates_created: int = 0
    skipped_empty: int = 0
    errors: list[str] = field(default_factory=list)


def _get_or_create_scraper_source(db: Session, owner_id: str) -> Source:
    """Ambil atau buat sumber data OSINT Scraper untuk pengguna."""
    source = (
        db.query(Source)
        .filter(Source.owner_id == owner_id, Source.name == "OSINT Scraper")
        .first()
    )
    if not source:
        source = Source(
            id=_uuid(),
            owner_id=owner_id,
            name="OSINT Scraper",
            access_type="AUTOMATED",
            weight=0.9,
            enabled=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def import_enriched_dataframe(
    db: Session, owner_id: str, df: pd.DataFrame, *, dry_run: bool = False
) -> EnrichedImportSummary:
    summary = EnrichedImportSummary(total_rows=len(df))
    if len(df) == 0:
        return summary

    source = _get_or_create_scraper_source(db, owner_id)

    # Cache alumni yang ada di DB milik user berdasarkan NIM dan Nama
    existing_alumni_by_nim: Dict[str, Alumni] = {
        a.nim.strip(): a
        for a in db.query(Alumni).filter(Alumni.owner_id == owner_id).all()
        if a.nim
    }
    existing_alumni_by_name: Dict[str, Alumni] = {
        a.full_name.strip().lower(): a
        for a in db.query(Alumni).filter(Alumni.owner_id == owner_id).all()
    }

    for idx, row in df.iterrows():
        excel_row = idx + 2
        name = str(row.get("Nama Lulusan") or "").strip()
        nim = str(row.get("NIM") or "").strip()

        if not name and not nim:
            summary.skipped_empty += 1
            continue

        # Ekstraksi field pengayaan
        linkedin = str(row.get("LinkedIn") or "").strip()
        instagram = str(row.get("Instagram") or "").strip()
        facebook = str(row.get("Facebook") or "").strip()
        tiktok = str(row.get("TikTok") or "").strip()
        email = str(row.get("Email") or "").strip()
        phone = str(row.get("No HP") or "").strip()
        employer = str(row.get("Tempat Bekerja") or "").strip()
        address = str(row.get("Alamat Bekerja") or "").strip()
        position = str(row.get("Posisi") or "").strip()
        sector = str(row.get("Kategori Sektor") or "").strip()
        company_social = str(row.get("Medsos / Web Tempat Bekerja") or "").strip()

        # Cek apakah ada data temuan
        has_enrichment = any([
            linkedin, instagram, facebook, tiktok, email, phone,
            employer, address, position, company_social,
            (sector and sector != "Belum Teridentifikasi")
        ])

        # 1. Temukan atau buat Alumni
        alumni = None
        if nim and nim in existing_alumni_by_nim:
            alumni = existing_alumni_by_nim[nim]
        elif name.lower() in existing_alumni_by_name:
            alumni = existing_alumni_by_name[name.lower()]

        is_new_alumni = False
        if not alumni:
            is_new_alumni = True
            alumni = Alumni(
                id=_uuid(),
                owner_id=owner_id,
                full_name=name or f"Alumni {nim}",
                nim=nim,
                tahun_masuk=int(row["Tahun Masuk"]) if pd.notna(row.get("Tahun Masuk")) and str(row["Tahun Masuk"]).isdigit() else None,
                tanggal_lulus=parse_tanggal(row.get("Tanggal Lulus")),
                fakultas=str(row.get("Fakultas") or "").strip(),
                program_studi=str(row.get("Program Studi") or "").strip(),
                name_variations=json.dumps([]),
                status="BELUM_DILACAK",
            )
            if not dry_run:
                db.add(alumni)
                db.flush()
            if nim:
                existing_alumni_by_nim[nim] = alumni
            existing_alumni_by_name[alumni.full_name.lower()] = alumni
            summary.alumni_created += 1
        else:
            summary.alumni_updated += 1

        # 2. Simpan atau perbarui Candidate jika ada data temuan
        if has_enrichment:
            # Standarisasi sektor (PNS, Swasta, Wirausaha)
            emp_type = ""
            if "PNS" in sector or "ASN" in sector:
                emp_type = "PNS"
            elif "Wirausaha" in sector:
                emp_type = "Wirausaha"
            elif "Swasta" in sector:
                emp_type = "Swasta"

            candidate = (
                db.query(Candidate)
                .filter(Candidate.alumni_id == alumni.id, Candidate.source_id == source.id)
                .first()
            )
            if not candidate:
                candidate = Candidate(
                    id=_uuid(),
                    alumni_id=alumni.id,
                    source_id=source.id,
                    raw_name=name,
                    linkedin_url=linkedin,
                    instagram_url=instagram,
                    facebook_url=facebook,
                    tiktok_url=tiktok,
                    email=email,
                    phone=phone,
                    employer_name=employer,
                    employer_address=address,
                    position=position,
                    employment_type=emp_type,
                    employer_social_media=company_social,
                    match_score=95.0,
                    name_score=95.0,
                    review_status="ACCEPTED",
                    reviewed_at=_now(),
                    fetched_at=_now(),
                )
                if not dry_run:
                    db.add(candidate)
                    db.flush()
                summary.candidates_created += 1
            else:
                # Perbarui field yang ada
                if linkedin: candidate.linkedin_url = linkedin
                if instagram: candidate.instagram_url = instagram
                if facebook: candidate.facebook_url = facebook
                if tiktok: candidate.tiktok_url = tiktok
                if email: candidate.email = email
                if phone: candidate.phone = phone
                if employer: candidate.employer_name = employer
                if address: candidate.employer_address = address
                if position: candidate.position = position
                if emp_type: candidate.employment_type = emp_type
                if company_social: candidate.employer_social_media = company_social
                candidate.match_score = 95.0
                candidate.review_status = "ACCEPTED"
                candidate.reviewed_at = _now()

            # Hubungkan alumni dengan kandidat terkonfirmasi
            if not dry_run:
                alumni.confirmed_candidate_id = candidate.id
                alumni.status = "TERVERIFIKASI_OTOMATIS"
                alumni.last_verified_at = _now()

    if not dry_run:
        db.commit()

    return summary


def import_enriched_file(
    db: Session, owner_id: str, content: bytes, filename: str, *, dry_run: bool = False
) -> EnrichedImportSummary:
    buffer = io.BytesIO(content)
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(buffer, dtype=str)
    else:
        df = pd.read_excel(buffer, dtype=str)
    return import_enriched_dataframe(db, owner_id, df, dry_run=dry_run)
