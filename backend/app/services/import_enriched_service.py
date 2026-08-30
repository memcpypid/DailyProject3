"""
Layanan Impor Data Hasil Scraping / Enrichment (DailyProject4 -> DailyProject3)
Dioptimasi dengan batch querying agar proses ribuan data selesai dalam hitungan detik.
"""

from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

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


def _clean_str(v: Any) -> str:
    if pd.isna(v) or v is None:
        return ""
    s = str(v).strip()
    if s.lower() in ("nan", "none", "null", "undefined"):
        return ""
    return s


def import_enriched_dataframe(
    db: Session, owner_id: str, df: pd.DataFrame, *, dry_run: bool = False
) -> EnrichedImportSummary:
    summary = EnrichedImportSummary(total_rows=len(df))
    if len(df) == 0:
        return summary

    source = _get_or_create_scraper_source(db, owner_id)

    # 1. Kumpulkan semua NIM & Nama dari file yang diunggah
    nims_in_file = set()
    names_in_file = set()
    for _, row in df.iterrows():
        nim = _clean_str(row.get("NIM"))
        name = _clean_str(row.get("Nama Lulusan")).lower()
        if nim:
            nims_in_file.add(nim)
        if name:
            names_in_file.add(name)

    # 2. Query HANYA data alumni yang cocok dari DB (bukan seluruh 142k alumni!)
    matched_alumni_list: List[Alumni] = []
    if nims_in_file:
        nim_list = list(nims_in_file)
        chunk_size = 900
        for i in range(0, len(nim_list), chunk_size):
            chunk = nim_list[i : i + chunk_size]
            matched_alumni_list.extend(
                db.query(Alumni)
                .filter(Alumni.owner_id == owner_id, Alumni.nim.in_(chunk))
                .all()
            )

    alumni_by_nim: Dict[str, Alumni] = {a.nim.strip(): a for a in matched_alumni_list if a.nim}
    alumni_by_name: Dict[str, Alumni] = {a.full_name.strip().lower(): a for a in matched_alumni_list}

    # 3. Pre-fetch semua candidate terkait alumni yang cocok dalam 1 query batch
    alumni_ids = [a.id for a in matched_alumni_list]
    candidates_by_alumni_id: Dict[str, Candidate] = {}
    if alumni_ids:
        chunk_size = 900
        for i in range(0, len(alumni_ids), chunk_size):
            chunk = alumni_ids[i : i + chunk_size]
            for c in (
                db.query(Candidate)
                .filter(Candidate.alumni_id.in_(chunk), Candidate.source_id == source.id)
                .all()
            ):
                candidates_by_alumni_id[c.alumni_id] = c

    # 4. Iterasi dan proses update secara instan dalam memori
    now_ts = _now()

    for idx, row in df.iterrows():
        name = _clean_str(row.get("Nama Lulusan"))
        nim = _clean_str(row.get("NIM"))

        if not name and not nim:
            summary.skipped_empty += 1
            continue

        linkedin = _clean_str(row.get("LinkedIn"))
        instagram = _clean_str(row.get("Instagram"))
        facebook = _clean_str(row.get("Facebook"))
        tiktok = _clean_str(row.get("TikTok"))
        email = _clean_str(row.get("Email"))
        phone = _clean_str(row.get("No HP"))
        employer = _clean_str(row.get("Tempat Bekerja"))
        address = _clean_str(row.get("Alamat Bekerja"))
        position = _clean_str(row.get("Posisi"))
        sector = _clean_str(row.get("Kategori Sektor"))
        company_social = _clean_str(row.get("Medsos / Web Tempat Bekerja"))

        has_enrichment = any([
            linkedin, instagram, facebook, tiktok, email, phone,
            employer, address, position, company_social,
            (sector and sector != "Belum Teridentifikasi")
        ])

        # Cari alumni yang cocok
        alumni = None
        if nim and nim in alumni_by_nim:
            alumni = alumni_by_nim[nim]
        elif name.lower() in alumni_by_name:
            alumni = alumni_by_name[name.lower()]

        if not alumni:
            # Buat alumni baru jika belum ada di database
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
                created_at=now_ts,
                updated_at=now_ts,
            )
            if not dry_run:
                db.add(alumni)
            if nim:
                alumni_by_nim[nim] = alumni
            alumni_by_name[alumni.full_name.lower()] = alumni
            summary.alumni_created += 1
        else:
            summary.alumni_updated += 1

        # Perbarui Candidate / Profil Temuan
        if has_enrichment:
            emp_type = ""
            if "PNS" in sector or "ASN" in sector:
                emp_type = "PNS"
            elif "Wirausaha" in sector:
                emp_type = "Wirausaha"
            elif "Swasta" in sector:
                emp_type = "Swasta"

            candidate = candidates_by_alumni_id.get(alumni.id)
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
                    reviewed_at=now_ts,
                    fetched_at=now_ts,
                )
                if not dry_run:
                    db.add(candidate)
                candidates_by_alumni_id[alumni.id] = candidate
                summary.candidates_created += 1
            else:
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
                candidate.reviewed_at = now_ts

            if not dry_run:
                alumni.confirmed_candidate_id = candidate.id
                alumni.status = "TERVERIFIKASI_OTOMATIS"
                alumni.last_verified_at = now_ts
                alumni.updated_at = now_ts

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
