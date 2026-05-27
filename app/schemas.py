from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GeospatialContext(BaseModel):
    location_label: str | None = Field(default=None, max_length=120)
    route_description: str | None = Field(default=None, max_length=280)
    time_of_day: Literal["day", "night", "dawn", "dusk"] | None = None
    known_hazards: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="Up to 8 known hazard tags to bias conservative risk scoring.",
    )
    mobility_aid: str | None = Field(default=None, max_length=80)


class GuidanceRequest(BaseModel):
    scene_description: str = Field(..., min_length=5, max_length=2000)
    geospatial_context: GeospatialContext | None = None

    @field_validator("scene_description")
    @classmethod
    def validate_scene_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("scene_description cannot be empty")
        return cleaned


class FallbackGuidanceRequest(GuidanceRequest):
    reason: str | None = Field(default=None, max_length=120)


class GuidanceResponse(BaseModel):
    guidance_text: str
    safety_notes: str
    confidence_notes: str
    mode: Literal["qwen", "fallback"] = "qwen"
    fallback_reason: str | None = None
    risk_score: int = Field(default=35, ge=0, le=100)


class ImageAnalysisResponse(GuidanceResponse):
    image_summary: str
    extracted_text: str | None = None


class EdgeContextRequest(BaseModel):
    obstacle_distance_m: float | None = Field(default=None, ge=0, le=20)
    ambient_noise_db: float | None = Field(default=None, ge=0, le=140)
    motion_state: Literal["still", "walking", "running", "vehicle"] | None = None
    gps_accuracy_m: float | None = Field(default=None, ge=0, le=200)
    battery_level: float | None = Field(default=None, ge=0, le=100)


class EdgeContextResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_band: Literal["low", "medium", "high"]
    suggested_actions: list[str]
    edge_ready: bool = True


class SessionHistoryItem(BaseModel):
    id: str
    created_at: str
    source: Literal["guidance", "fallback", "image", "manual"]
    scene_description: str = Field(min_length=1, max_length=2000)
    guidance: GuidanceResponse
    pinned: bool = False


class SessionHistoryResponse(BaseModel):
    items: list[SessionHistoryItem]


class SessionHistoryCreateRequest(BaseModel):
    source: Literal["manual"] = "manual"
    scene_description: str = Field(min_length=1, max_length=2000)
    guidance: GuidanceResponse
    pinned: bool = False


class ErrorResponse(BaseModel):
    error: str
    detail: str
    request_id: str | None = None
