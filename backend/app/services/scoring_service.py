"""Penilaian identitas transparan dengan bobot dari rancangan Daily Project 2."""

import re
import unicodedata
import json
from difflib import SequenceMatcher


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, _normalise(left), _normalise(right)).ratio() * 100


def score_candidate(alumni, fields: dict, source_weight: float = 0.5) -> dict[str, float]:
    try:
        variations = json.loads(alumni.name_variations or "[]")
    except (TypeError, ValueError):
        variations = []
    names = [alumni.full_name, *variations]
    raw_name = fields.get("raw_name", "")
    name = max((_similarity(raw_name, item) for item in names), default=0.0)

    evidence = " ".join(str(fields.get(key, "")) for key in (
        "snippet", "employer_name", "employer_address", "position", "email"
    ))
    normalised_evidence = _normalise(evidence)
    affiliation_terms = [alumni.fakultas, alumni.program_studi, "UMM", "Universitas Muhammadiyah Malang"]
    affiliation = 100.0 if any(_normalise(term) in normalised_evidence for term in affiliation_terms if term) else source_weight * 60

    graduation_year = alumni.tanggal_lulus.year if alumni.tanggal_lulus else None
    years = [int(year) for year in re.findall(r"\b(?:19|20)\d{2}\b", evidence)]
    timeline = 100.0 if graduation_year and any(year >= graduation_year - 1 for year in years) else (50.0 if not years else 0.0)

    study_words = {word for word in _normalise(alumni.program_studi).split() if len(word) > 3}
    work_words = set(_normalise(f"{fields.get('position', '')} {fields.get('snippet', '')}").split())
    field = 100.0 if study_words & work_words else (50.0 if not study_words or not work_words else 20.0)

    total = name * 0.40 + affiliation * 0.30 + timeline * 0.15 + field * 0.15
    return {
        "name_score": round(name, 2),
        "affiliation_score": round(affiliation, 2),
        "timeline_score": round(timeline, 2),
        "field_score": round(field, 2),
        "match_score": round(total, 2),
    }
