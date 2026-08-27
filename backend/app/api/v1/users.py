from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.security import hash_password
from app.infrastructure.db import get_db
from app.infrastructure.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import SuccessResponse
from app.schemas.user import UpdateProfileRequest, UserResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=SuccessResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return SuccessResponse(message="Profil pengguna", data=UserResponse.model_validate(current_user))


@router.put("/me", response_model=SuccessResponse[UserResponse])
def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fields: dict = {}
    if payload.name:
        fields["name"] = payload.name
    if payload.password:
        fields["password_hash"] = hash_password(payload.password)
    user = UserRepository(db).update(current_user, **fields)
    return SuccessResponse(message="Profil berhasil diperbarui", data=UserResponse.model_validate(user))
