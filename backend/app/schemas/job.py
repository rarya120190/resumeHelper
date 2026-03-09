from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Request ─────────────────────────────────────────────────────────────
class JobDescriptionCreate(BaseModel):
    """Accepts job description via text, url, or file content."""

    raw_text: Optional[str] = Field(None, min_length=1)
    source_url: Optional[str] = Field(None, max_length=2048)
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)


# ── Normalized structure ────────────────────────────────────────────────
class NormalizedJD(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    nice_to_haves: list[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    benefits: list[str] = Field(default_factory=list)


# ── Response ────────────────────────────────────────────────────────────
class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    normalized_json: Optional[dict[str, Any]] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    source_url: Optional[str] = None
    company_brief: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
