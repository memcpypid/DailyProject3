from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.candidate import CandidateResponse


class AlumniCreateRequest(BaseModel):
    full_name: str  # Nama Lulusan
    nim: str = ""
    tahun_masuk: int | None = None
    tanggal_lulus: date | None = None
    fakultas: str = ""
    program_studi: str = ""
    name_variations: list[str] = []

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Nama alumni tidak boleh kosong")
        return value.strip()


class AlumniUpdateRequest(BaseModel):
    full_name: str | None = None
    nim: str | None = None
    tahun_masuk: int | None = None
    tanggal_lulus: date | None = None
    fakultas: str | None = None
    program_studi: str | None = None
    name_variations: list[str] | None = None


class AlumniImportResponse(BaseModel):
    total_rows: int
    created: int
    skipped_duplicate: int
    skipped_duplicate_in_file: int
    skipped_duplicate_in_db: int
    skipped_invalid: int
    errors: list[str]


class AlumniResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    nim: str
    tahun_masuk: int | None
    tanggal_lulus: date | None
    fakultas: str
    program_studi: str
    name_variations: list[str]
    status: str
    confirmed_candidate_id: str | None
    confirmed_profile: CandidateResponse | None = None
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
