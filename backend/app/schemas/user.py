from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    password: str | None = None
