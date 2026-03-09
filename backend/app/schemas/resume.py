from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Master Resume ───────────────────────────────────────────────────────
class MasterResumeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class MasterResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    parsed_json: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Tailored Resume ────────────────────────────────────────────────────
class TailorRequest(BaseModel):
    master_resume_id: uuid.UUID
    job_description_id: uuid.UUID


class QAResult(BaseModel):
    qa_status: str
    qa_score: Optional[float] = None
    confidence_scores: Optional[dict[str, Any]] = None
    issues: list[str] = Field(default_factory=list)


class TailoredResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    master_resume_id: uuid.UUID
    job_description_id: uuid.UUID
    content: str
    qa_status: str
    qa_score: Optional[float] = None
    confidence_scores: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
