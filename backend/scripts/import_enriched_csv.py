#!/usr/bin/env python3
"""
CLI untuk Mengimpor Data Hasil Scraping (Enriched Data) ke Alumni Tracker (DailyProject3)

Pemakaian:
    python scripts/import_enriched_csv.py --file ../DailyProject4/Hasil_Semua_Alumni.csv --email darmaputra443@gmail.com
    python scripts/import_enriched_csv.py --file ../DailyProject4/Hasil_Semua_Alumni.csv --email darmaputra443@gmail.com --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.db import SessionLocal, migrate_sqlite_schema
from app.infrastructure.models import User
from app.services.import_enriched_service import import_enriched_file


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--file", "-f", required=True, help="Path ke file .csv / .xlsx hasil scraping")
    parser.add_argument("--email", "-e", required=True, help="Email akun tujuan di DailyProject3")
    parser.add_argument("--dry-run", action="store_true", help="Hanya tampilkan simulasi, tidak menyimpan ke DB")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"❌ File tidak ditemukan: {path}", file=sys.stderr)
        sys.exit(1)

    migrate_sqlite_schema()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email.lower()).first()
        if not user:
            print(f"❌ Akun dengan email '{args.email}' tidak ditemukan di database.", file=sys.stderr)
            sys.exit(1)

        print(f"📂 Membaca file: {path.name}...")
        content = path.read_bytes()
        summary = import_enriched_file(db, user.id, content, path.name, dry_run=args.dry_run)

        print("\n" + "="*60)
        print("📊 HASIL IMPOR DATA PENGAYAAN ALUMNI (OSINT):")
        print("="*60)
        print(f" • Total Baris di File      : {summary.total_rows:,}")
        print(f" • Data Alumni Baru Dibuat  : {summary.alumni_created:,}")
        print(f" • Data Alumni Diperbarui   : {summary.alumni_updated:,}")
        print(f" • Profil Temuan Diperkaya  : {summary.candidates_created:,}")
        if summary.skipped_empty:
            print(f" • Baris Kosong Dilewati    : {summary.skipped_empty:,}")
        print("="*60)

        if args.dry_run:
            print("ℹ️ Mode --dry-run: Tidak ada data yang diubah di database.")
        else:
            print(f"✅ Selesai! Data berhasil diimpor & dihubungkan ke akun '{args.email}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
