"""
Layanan Auto-Scraping & OSINT Data Enrichment (DailyProject3 Backend Engine)
Menjalankan pencarian paralel multi-worker secara asinkron di latar belakang
dan langsung menyimpan hasilnya ke database serta menyajikan live log ke antarmuka pengguna.
"""

from __future__ import annotations

import collections
import concurrent.futures
import json
import logging
import random
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.infrastructure.db import SessionLocal
from app.infrastructure.models import Alumni, Candidate, Source, _now, _uuid

logger = logging.getLogger("AutoScraperService")

# Silence external library logs
for noisy in ["ddgs", "primp", "urllib3", "curl_cffi", "requests"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

# Regex patterns
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+62|62|08)[0-9\-\s]{8,15}')
WA_LINK_REGEX = re.compile(r'(?:https?://)?(?:wa\.me|api\.whatsapp\.com/send\?phone=)([0-9+]+)')
LINKEDIN_REGEX = re.compile(r'https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([a-zA-Z0-9%_-]+)')
INSTAGRAM_REGEX = re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)')
FACEBOOK_REGEX = re.compile(r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9._-]+)')
TIKTOK_REGEX = re.compile(r'https?://(?:www\.)?tiktok\.com/@([a-zA-Z0-9._]+)')

SOCIAL_BLACKLIST = {
    "login", "signup", "p", "reel", "stories", "explore", "about", "terms",
    "privacy", "help", "direct", "feed", "sharer", "share", "home", "search",
    "groups", "events", "marketplace", "watch", "legal", "company", "jobs"
}

PNS_KEYWORDS = [
    "pns", "pegawai negeri", "asn", "aparatur sipil", "kementerian", "dinas",
    "pemda", "pemkab", "pemkot", "pemprov", "kantor bupati", "kantor walikota",
    "kecamatan", "kelurahan", "puskesmas", "rsud", "guru pns", "kejaksaan",
    "bkn", "bps", "bappeda", "setda", "kemenag", "kemendikbud", "kemenkeu"
]

WIRAUSAHA_KEYWORDS = [
    "owner", "founder", "co-founder", "pemilik", "wirausaha", "entrepreneur",
    "freelancer", "freelance", "kedai", "warung", "toko", "boutique", "studio",
    "bisnis sendiri", "founder & ceo", "co founder", "self-employed"
]

SWASTA_KEYWORDS = [
    "pt.", "pt ", "tbk", "cv.", "cv ", "bank", "corp", "corporation", "inc",
    "ltd", "consulting", "software", "tech", "indonesia", "astra", "telkom",
    "shopee", "tokopedia", "gojek", "grab", "bca", "mandiri", "bri", "bni",
    "perusahaan", "kantor", "agency", "firm", "holding"
]


class AlumniSearchWorker:
    """Worker instans scraper per-thread."""

    def __init__(self, delay_min: float = 0.8, delay_max: float = 2.0, univ_keyword: str = ""):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.univ_keyword = univ_keyword.strip()
        self.ddgs = DDGS() if DDGS else None

    def _sleep(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def search_query(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        if not self.ddgs:
            return []
        try:
            self._sleep()
            return list(self.ddgs.text(query, max_results=max_results)) or []
        except Exception:
            try:
                time.sleep(1.5)
                self.ddgs = DDGS()
                return list(self.ddgs.text(query, max_results=max_results)) or []
            except Exception:
                return []

    def extract_social_links(self, search_results: List[Dict[str, str]]) -> Dict[str, str]:
        socials = {"linkedin": "", "instagram": "", "facebook": "", "tiktok": ""}
        for item in search_results:
            href = item.get("href", "") or ""
            if not socials["linkedin"]:
                m = LINKEDIN_REGEX.search(href)
                if m and m.group(1).lower() not in SOCIAL_BLACKLIST:
                    socials["linkedin"] = href.split("?")[0]
            if not socials["instagram"]:
                m = INSTAGRAM_REGEX.search(href)
                if m and m.group(1).lower() not in SOCIAL_BLACKLIST:
                    socials["instagram"] = href.split("?")[0]
            if not socials["facebook"]:
                m = FACEBOOK_REGEX.search(href)
                if m and m.group(1).lower() not in SOCIAL_BLACKLIST:
                    socials["facebook"] = href.split("?")[0]
            if not socials["tiktok"]:
                m = TIKTOK_REGEX.search(href)
                if m and m.group(1).lower() not in SOCIAL_BLACKLIST:
                    socials["tiktok"] = href.split("?")[0]
        return socials

    def extract_emails(self, texts: List[str]) -> List[str]:
        found = set()
        for text in texts:
            if not text: continue
            for m in EMAIL_REGEX.findall(text):
                if not any(m.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".js"]):
                    found.add(m.strip(".,;:()<>"))
        return list(found)

    def extract_phone_numbers(self, texts: List[str]) -> List[str]:
        found = set()
        for text in texts:
            if not text: continue
            for wa in WA_LINK_REGEX.findall(text):
                clean_wa = re.sub(r'[^0-9]', '', wa)
                if len(clean_wa) >= 9:
                    found.add(clean_wa)
            for m in PHONE_REGEX.findall(text):
                clean = re.sub(r'[\s\-]', '', m)
                if 9 <= len(clean) <= 15:
                    found.add(clean)
        return list(found)

    def parse_job_and_company(self, titles_and_snippets: List[Dict[str, str]]) -> Dict[str, str]:
        job_info = {
            "tempat_bekerja": "",
            "posisi": "",
            "alamat_bekerja": "",
            "kategori_pekerjaan": "Belum Teridentifikasi",
            "medsos_kantor": ""
        }

        def clean_val(v: str) -> str:
            v = re.sub(r'[\.]{2,}', '', v).strip(" .,-–|/\\")
            return v if len(v) >= 2 else ""

        for item in titles_and_snippets:
            title = item.get("title", "")
            body = item.get("body", "")
            full_text = f"{title} {body}"

            if "linkedin.com" in item.get("href", ""):
                clean_title = re.sub(r'\s*\|\s*LinkedIn.*$', '', title, flags=re.IGNORECASE)
                parts = clean_title.split(" - ")
                if len(parts) >= 2:
                    potential = parts[1]
                    if " at " in potential:
                        r, c = potential.split(" at ", 1)
                        if not job_info["posisi"]: job_info["posisi"] = clean_val(r)
                        if not job_info["tempat_bekerja"]: job_info["tempat_bekerja"] = clean_val(c)
                    elif " di " in potential:
                        r, c = potential.split(" di ", 1)
                        if not job_info["posisi"]: job_info["posisi"] = clean_val(r)
                        if not job_info["tempat_bekerja"]: job_info["tempat_bekerja"] = clean_val(c)
                    else:
                        if not job_info["posisi"]: job_info["posisi"] = clean_val(potential)

            work_patterns = [
                r'(?:bekerja sebagai|sebagai|posisi|jabatan)\s+([A-Za-z\s]{3,30})\s+(?:di|pada|at)\s+([A-Za-z0-9\.\s\-]{3,40})',
                r'([A-Za-z\s]{3,30})\s+(?:at|di)\s+((?:PT|CV|Kantor|Dinas|Kementerian|Bank|Universitas|RSUD)\s+[A-Za-z0-9\.\s\-]{3,40})'
            ]
            for pat in work_patterns:
                m = re.search(pat, full_text, re.IGNORECASE)
                if m:
                    pos, comp = clean_val(m.group(1)), clean_val(m.group(2))
                    if not job_info["posisi"] and 3 <= len(pos) <= 40: job_info["posisi"] = pos
                    if not job_info["tempat_bekerja"] and 3 <= len(comp) <= 50: job_info["tempat_bekerja"] = comp

            cities = ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Malang", "Yogyakarta", "Solo", "Denpasar", "Makassar", "Palembang", "Balikpapan", "Samarinda", "Batam", "Tangerang", "Bekasi", "Depok", "Bogor", "Sidoarjo"]
            for city in cities:
                if re.search(r'\b' + city + r'\b', full_text, re.IGNORECASE):
                    if not job_info["alamat_bekerja"]:
                        job_info["alamat_bekerja"] = city
                    break

        job_info["tempat_bekerja"] = clean_val(job_info["tempat_bekerja"])
        job_info["posisi"] = clean_val(job_info["posisi"])

        combined_text = f"{job_info['tempat_bekerja']} {job_info['posisi']}".lower()
        if any(k in combined_text for k in PNS_KEYWORDS):
            job_info["kategori_pekerjaan"] = "PNS"
        elif any(k in combined_text for k in WIRAUSAHA_KEYWORDS):
            job_info["kategori_pekerjaan"] = "Wirausaha"
        elif any(k in combined_text for k in SWASTA_KEYWORDS) or job_info["tempat_bekerja"]:
            job_info["kategori_pekerjaan"] = "Swasta"

        return job_info

    def find_company_socials(self, company_name: str) -> str:
        clean_name = re.sub(r'[\.]{2,}', '', company_name).strip(" .,-–|/\\")
        if not clean_name or len(clean_name) < 3 or clean_name.lower() in ["pt", "cv", "indonesia"]:
            return ""
        try:
            results = self.search_query(f'"{clean_name}" official website OR linkedin OR instagram', max_results=2)
            links = [r.get("href", "") for r in results if r.get("href", "") and not any(r.get("href", "").endswith(ext) for ext in [".pdf", ".doc", ".docx"])]
            return " | ".join(links[:2])
        except Exception:
            return ""

    def search_alumni(self, name: str, nim: str = "", prodi: str = "", fakultas: str = "") -> Dict[str, Any]:
        univ_str = f" {self.univ_keyword}" if self.univ_keyword else ""
        prodi_str = f" {prodi}" if prodi else ""

        # 1. Social search
        social_q = f'"{name}"{prodi_str}{univ_str} (linkedin OR instagram OR facebook OR tiktok)'
        social_results = self.search_query(social_q, max_results=5)
        socials = self.extract_social_links(social_results)

        if not socials["linkedin"]:
            li_results = self.search_query(f'"{name}"{prodi_str}{univ_str} site:linkedin.com/in', max_results=3)
            li_socials = self.extract_social_links(li_results)
            socials["linkedin"] = li_socials["linkedin"]
            social_results.extend(li_results)

        # 2. Contact & Workplace search
        contact_q = f'"{name}"{prodi_str}{univ_str} (email OR "gmail.com" OR "wa.me" OR "08" OR "kantor" OR "bekerja di" OR "posisi")'
        contact_results = self.search_query(contact_q, max_results=4)

        all_results = social_results + contact_results
        snippets = [f"{r.get('title', '')} {r.get('body', '')}" for r in all_results]

        emails = self.extract_emails(snippets)
        phones = self.extract_phone_numbers(snippets)
        job_info = self.parse_job_and_company(all_results)

        if job_info["tempat_bekerja"]:
            job_info["medsos_kantor"] = self.find_company_socials(job_info["tempat_bekerja"])

        return {
            "linkedin_url": socials.get("linkedin", ""),
            "instagram_url": socials.get("instagram", ""),
            "facebook_url": socials.get("facebook", ""),
            "tiktok_url": socials.get("tiktok", ""),
            "email": ", ".join(emails) if emails else "",
            "phone": ", ".join(phones) if phones else "",
            "employer_name": job_info.get("tempat_bekerja", ""),
            "employer_address": job_info.get("alamat_bekerja", ""),
            "position": job_info.get("posisi", ""),
            "employment_type": job_info.get("kategori_pekerjaan", ""),
            "employer_social_media": job_info.get("medsos_kantor", ""),
        }


class AutoScraperManager:
    """Manajer sesi background scraping untuk aplikasi DailyProject3."""

    def __init__(self):
        self._lock = threading.Lock()
        self.is_running = False
        self.stop_requested = False
        self.owner_id = ""
        self.workers = 10
        self.total_queued = 0
        self.processed_count = 0
        self.found_count = 0
        self.start_time: Optional[float] = None
        self.current_alumni_name = ""
        self.logs = collections.deque(maxlen=200)  # Menyimpan 200 log aktivitas terakhir
        self._thread: Optional[threading.Thread] = None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = int(time.time() - self.start_time) if (self.is_running and self.start_time) else 0
            percent = (self.processed_count / self.total_queued * 100) if self.total_queued > 0 else 0.0
            return {
                "is_running": self.is_running,
                "stop_requested": self.stop_requested,
                "workers": self.workers,
                "total_queued": self.total_queued,
                "processed_count": self.processed_count,
                "found_count": self.found_count,
                "progress_percent": round(percent, 1),
                "elapsed_seconds": elapsed,
                "current_name": self.current_alumni_name,
            }

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            all_logs = list(self.logs)
            return all_logs[-limit:]

    def stop(self):
        with self._lock:
            if self.is_running:
                self.stop_requested = True
                self._add_log({
                    "type": "system",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": "Permintaan penghentian scraping diterima. Menunggu worker menyelesaikan tugas berjalan...",
                })

    def _add_log(self, entry: Dict[str, Any]):
        self.logs.append(entry)

    def start(
        self,
        owner_id: str,
        workers: int = 10,
        limit: Optional[int] = 50,
        status_filter: Optional[str] = "BELUM_DILACAK",
        univ_keyword: str = "",
        delay_min: float = 0.8,
        delay_max: float = 2.0,
    ) -> bool:
        with self._lock:
            if self.is_running:
                return False

            self.is_running = True
            self.stop_requested = False
            self.owner_id = owner_id
            self.workers = max(1, min(workers, 20))
            self.processed_count = 0
            self.found_count = 0
            self.start_time = time.time()
            self.logs.clear()

            self._add_log({
                "type": "system",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "message": f"🚀 Memulai Auto-Scraping OSINT Bot dengan {self.workers} Worker paralel...",
            })

            # Mulai thread background
            self._thread = threading.Thread(
                target=self._run_scraper_loop,
                args=(owner_id, self.workers, limit, status_filter, univ_keyword, delay_min, delay_max),
                daemon=True,
            )
            self._thread.start()
            return True

    def _run_scraper_loop(
        self,
        owner_id: str,
        num_workers: int,
        limit: Optional[int],
        status_filter: Optional[str],
        univ_keyword: str,
        delay_min: float,
        delay_max: float,
    ):
        db = SessionLocal()
        tasks = []
        try:
            # 1. Ambil sumber data OSINT Scraper
            source = db.query(Source).filter(Source.owner_id == owner_id, Source.name == "OSINT Scraper").first()
            if not source:
                source = Source(
                    id=_uuid(),
                    owner_id=owner_id,
                    name="OSINT Scraper",
                    access_type="AUTOMATED",
                    weight=0.95,
                    enabled=True,
                )
                db.add(source)
                db.commit()
                db.refresh(source)

            # 2. Query target alumni
            query = db.query(Alumni).filter(Alumni.owner_id == owner_id)
            if status_filter:
                query = query.filter(Alumni.status == status_filter)
            
            alumni_list = query.all()
            if limit and limit > 0:
                alumni_list = alumni_list[:limit]

            with self._lock:
                self.total_queued = len(alumni_list)
                self._add_log({
                    "type": "system",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"📊 Ditemukan {len(alumni_list):,} alumni untuk diproses.",
                })

            if not alumni_list:
                with self._lock:
                    self.is_running = False
                    self._add_log({
                        "type": "system",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "message": "Tidak ada data alumni yang perlu diproses.",
                    })
                return

            tasks = [{"id": a.id, "name": a.full_name, "nim": a.nim, "prodi": a.program_studi, "fakultas": a.fakultas} for a in alumni_list]

        finally:
            db.close()

        # Thread local scraper
        thread_local = threading.local()

        def get_scraper():
            if not hasattr(thread_local, "worker"):
                thread_local.worker = AlumniSearchWorker(delay_min=delay_min, delay_max=delay_max, univ_keyword=univ_keyword)
            return thread_local.worker

        def process_one(item: Dict[str, str]):
            if self.stop_requested:
                return

            worker = get_scraper()
            with self._lock:
                self.current_alumni_name = item["name"]

            # Cari data OSINT
            result = worker.search_alumni(
                name=item["name"],
                nim=item.get("nim", ""),
                prodi=item.get("prodi", ""),
                fakultas=item.get("fakultas", ""),
            )

            has_found = any([
                result.get("linkedin_url"),
                result.get("instagram_url"),
                result.get("facebook_url"),
                result.get("tiktok_url"),
                result.get("email"),
                result.get("phone"),
                result.get("employer_name"),
                result.get("position"),
            ])

            # Simpan langsung ke database
            db_task = SessionLocal()
            try:
                alumni_obj = db_task.query(Alumni).filter(Alumni.id == item["id"]).first()
                if alumni_obj:
                    if has_found:
                        source_obj = db_task.query(Source).filter(Source.owner_id == owner_id, Source.name == "OSINT Scraper").first()
                        cand = Candidate(
                            id=_uuid(),
                            alumni_id=alumni_obj.id,
                            source_id=source_obj.id if source_obj else "",
                            raw_name=item["name"],
                            linkedin_url=result.get("linkedin_url", ""),
                            instagram_url=result.get("instagram_url", ""),
                            facebook_url=result.get("facebook_url", ""),
                            tiktok_url=result.get("tiktok_url", ""),
                            email=result.get("email", ""),
                            phone=result.get("phone", ""),
                            employer_name=result.get("employer_name", ""),
                            employer_address=result.get("employer_address", ""),
                            position=result.get("position", ""),
                            employment_type=result.get("employment_type", ""),
                            employer_social_media=result.get("employer_social_media", ""),
                            match_score=95.0,
                            name_score=95.0,
                            review_status="ACCEPTED",
                            reviewed_at=_now(),
                            fetched_at=_now(),
                        )
                        db_task.add(cand)
                        db_task.flush()

                        alumni_obj.confirmed_candidate_id = cand.id
                        alumni_obj.status = "TERVERIFIKASI_OTOMATIS"
                        alumni_obj.last_verified_at = _now()
                    else:
                        alumni_obj.status = "TIDAK_DITEMUKAN"

                    db_task.commit()
            except Exception as save_err:
                logger.error(f"Gagal menyimpan temuan {item['name']}: {save_err}")
                db_task.rollback()
            finally:
                db_task.close()

            # Catat log
            with self._lock:
                self.processed_count += 1
                if has_found:
                    self.found_count += 1

                log_entry = {
                    "type": "result",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "alumni_id": item["id"],
                    "name": item["name"],
                    "nim": item["nim"],
                    "prodi": item["prodi"],
                    "has_found": has_found,
                    "linkedin": result.get("linkedin_url"),
                    "instagram": result.get("instagram_url"),
                    "facebook": result.get("facebook_url"),
                    "tiktok": result.get("tiktok_url"),
                    "email": result.get("email"),
                    "phone": result.get("phone"),
                    "employer": result.get("employer_name"),
                    "position": result.get("position"),
                    "sector": result.get("employment_type"),
                    "company_social": result.get("employer_social_media"),
                }
                self._add_log(log_entry)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_one, item) for item in tasks]
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_requested:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
        except Exception as e:
            logger.error(f"Error pada loop scraper: {e}")
        finally:
            with self._lock:
                self.is_running = False
                self.stop_requested = False
                self.current_alumni_name = ""
                self._add_log({
                    "type": "system",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "message": f"🏁 Selesai! {self.processed_count:,} alumni diproses, {self.found_count:,} profil berhasil diperkaya.",
                })


# Singleton manager instance
scraper_manager = AutoScraperManager()
