from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Sistem Pelacakan Alumni API"
    DATABASE_URL: str = "sqlite:///./alumni_tracker.db"

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CAMPUS_NAME: str = "Universitas Muhammadiyah Malang"

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # Pencarian web berbantuan manusia (fitur "Cari di Internet") - lihat
    # app/services/websearch_service.py. Kosongkan untuk menonaktifkan fitur ini.
    SERPAPI_KEY: str = ""
    SERPAPI_BASE_URL: str = "https://serpapi.com/search"


@lru_cache
def get_settings() -> Settings:
    return Settings()
