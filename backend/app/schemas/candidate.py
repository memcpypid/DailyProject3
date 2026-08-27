from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alumni_id: str
    source_id: str
    source_name: str
    raw_name: str

    linkedin_url: str
    instagram_url: str
    facebook_url: str
    tiktok_url: str
    email: str
    phone: str
    employer_name: str
    employer_address: str
    position: str
    employment_type: str
    employer_social_media: str

    snippet: str
    fetched_at: datetime

    @classmethod
    def from_model(cls, candidate) -> "CandidateResponse":
        return cls(
            id=candidate.id,
            alumni_id=candidate.alumni_id,
            source_id=candidate.source_id,
            source_name=candidate.source.name if candidate.source else "",
            raw_name=candidate.raw_name,
            linkedin_url=candidate.linkedin_url,
            instagram_url=candidate.instagram_url,
            facebook_url=candidate.facebook_url,
            tiktok_url=candidate.tiktok_url,
            email=candidate.email,
            phone=candidate.phone,
            employer_name=candidate.employer_name,
            employer_address=candidate.employer_address,
            position=candidate.position,
            employment_type=candidate.employment_type,
            employer_social_media=candidate.employer_social_media,
            snippet=candidate.snippet,
            fetched_at=candidate.fetched_at,
        )


class ManualCandidateRequest(BaseModel):
    """Input hasil riset manual (satu per satu, oleh manusia) untuk satu alumni."""

    source_id: str
    raw_name: str = ""
    linkedin_url: str = ""
    instagram_url: str = ""
    facebook_url: str = ""
    tiktok_url: str = ""
    email: str = ""
    phone: str = ""
    employer_name: str = ""
    employer_address: str = ""
    position: str = ""
    employment_type: str = ""
    employer_social_media: str = ""
    snippet: str = ""
