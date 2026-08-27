from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshResponse,
    TokenPair,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SuccessResponse[TokenPair])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        user = service.authenticate(payload.email, payload.password)
        access, refresh = service.issue_tokens(user)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token_pair = TokenPair(access_token=access, refresh_token=refresh, user=UserResponse.model_validate(user))
    return SuccessResponse(message="Login berhasil", data=token_pair)


@router.post("/refresh", response_model=SuccessResponse[RefreshResponse])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        access, refresh_token = service.refresh_tokens_pair(payload.refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return SuccessResponse(
        message="Token diperbarui", data=RefreshResponse(access_token=access, refresh_token=refresh_token)
    )


@router.post("/logout", response_model=SuccessResponse[None])
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(payload.refresh_token)
    return SuccessResponse(message="Logout berhasil", data=None)
