from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobDescription
from app.models.user import User
from app.schemas.job import JobDescriptionCreate, JobDescriptionResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    raw_text: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Create a job description from text, URL, or file upload."""
    text_content = raw_text

    # If a file was uploaded, read its text content
    if file is not None:
        file_bytes = await file.read()
        text_content = file_bytes.decode("utf-8", errors="replace")

    # If a URL was provided but no text, store it — scraping can happen asynchronously
    if not text_content and source_url:
        text_content = f"[Job posting URL: {source_url}]"

    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one of: raw_text, source_url, or file",
        )

    job = JobDescription(
        user_id=current_user.id,
        raw_text=text_content,
        source_url=source_url,
        company_name=company_name,
        job_title=job_title,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.get("/", response_model=list[JobDescriptionResponse])
async def list_job_descriptions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(JobDescription)
        .where(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == job_id,
            JobDescription.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return job
