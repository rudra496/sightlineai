from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GuidanceRequest(BaseModel):
    scene_description: str = Field(..., min_length=5, max_length=2000)

    @field_validator("scene_description")
    @classmethod
    def validate_scene_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("scene_description cannot be empty")
        return cleaned


class GuidanceResponse(BaseModel):
    guidance_text: str
    safety_notes: str
    confidence_notes: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
