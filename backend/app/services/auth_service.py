from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.infrastructure.models import User
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.services.source_service import SourceService

settings = get_settings()


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register(self, name: str, email: str, password: str) -> User:
        if self.users.get_by_email(email):
            raise AuthError("Email sudah terdaftar")
        user = self.users.create(name=name, email=email, password_hash=hash_password(password))
        # Registrasi Sumber Data & Bobot Kepercayaan (langkah 2) - seed default per akun baru
        SourceService(self.db).seed_defaults(user.id)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Email atau password salah")
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        payload = decode_token(refresh)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        self.refresh_tokens.create(user_id=user.id, jti=payload["jti"], expires_at=expires_at)
        return access, refresh

    def refresh_tokens_pair(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise AuthError("Refresh token tidak valid") from exc

        if payload.get("type") != "refresh":
            raise AuthError("Token bukan refresh token")

        stored = self.refresh_tokens.get_by_jti(payload["jti"])
        if not stored or stored.revoked:
            raise AuthError("Refresh token sudah tidak berlaku")
        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise AuthError("Refresh token sudah kedaluwarsa")

        user = self.users.get_by_id(payload["sub"])
        if not user:
            raise AuthError("Pengguna tidak ditemukan")

        # rotate: revoke old, issue new
        self.refresh_tokens.revoke(stored)
        return self.issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            return
        stored = self.refresh_tokens.get_by_jti(payload.get("jti", ""))
        if stored:
            self.refresh_tokens.revoke(stored)

    def get_user_from_access_token(self, token: str) -> User:
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise AuthError("Token tidak valid") from exc
        if payload.get("type") != "access":
            raise AuthError("Token bukan access token")
        user = self.users.get_by_id(payload["sub"])
        if not user:
            raise AuthError("Pengguna tidak ditemukan")
        return user
