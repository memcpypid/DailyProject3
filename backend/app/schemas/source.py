from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class SourceCreateRequest(BaseModel):
    name: str
    access_type: str = ""
    weight: float = 0.5
    enabled: bool = True

    @field_validator("weight")
    @classmethod
    def weight_in_range(cls, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise ValueError("Bobot kepercayaan harus di antara 0 dan 1")
        return value


class SourceUpdateRequest(BaseModel):
    name: str | None = None
    access_type: str | None = None
    weight: float | None = None
    enabled: bool | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    access_type: str
    weight: float
    enabled: bool
    created_at: datetime
    updated_at: datetime
