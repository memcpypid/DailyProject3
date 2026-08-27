"""CLI tipis untuk impor roster alumni - logika sesungguhnya ada di
app/services/import_service.py (dipakai bersama oleh endpoint API
`POST /api/v1/alumni/import` di aplikasi). Berguna untuk impor file besar
tanpa lewat HTTP, atau untuk automasi/cron di luar aplikasi.

Pemakaian:
    source venv/bin/activate
    python scripts/import_alumni.py --file /path/ke/Alumni.xlsx --email admin@kampus.ac.id
    python scripts/import_alumni.py --file /path/ke/Alumni.xlsx --email admin@kampus.ac.id --limit 100
    python scripts/import_alumni.py --file /path/ke/Alumni.xlsx --email admin@kampus.ac.id --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.db import SessionLocal  # noqa: E402
from app.infrastructure.models import User  # noqa: E402
from app.services.import_service import ImportError_, import_file  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="Path ke file .xlsx/.csv roster alumni")
    parser.add_argument("--email", required=True, help="Email akun tujuan (harus sudah terdaftar)")
    parser.add_argument("--limit", type=int, default=None, help="Batasi jumlah baris yang diimpor (untuk uji coba)")
    parser.add_argument("--dry-run", action="store_true", help="Hanya tampilkan ringkasan, tidak menyimpan ke DB")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File tidak ditemukan: {path}", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email.lower()).first()
        if not user:
            print(f"Akun dengan email {args.email} tidak ditemukan. Sediakan akun melalui administrator.", file=sys.stderr)
            sys.exit(1)

        try:
            summary = import_file(
                db, user.id, path.read_bytes(), path.name, limit=args.limit, dry_run=args.dry_run
            )
        except ImportError_ as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)

        print(f"Total baris di file: {summary.total_rows}")
        print(f"Baru: {summary.created}, duplikat dilewati: {summary.skipped_duplicate}, "
              f"tidak valid dilewati: {summary.skipped_invalid}")
        for err in summary.errors:
            print(f"  - {err}")

        if args.dry_run:
            print("Mode --dry-run: tidak ada perubahan yang disimpan.")
        else:
            print(f"Selesai. {summary.created} alumni ditambahkan ke akun {args.email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
