from __future__ import annotations

import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.resume import MasterResume, TailoredResume
from app.models.job import JobDescription
from app.models.user import User
from app.schemas.resume import (
    MasterResumeCreate,
    MasterResumeResponse,
    TailorRequest,
    TailoredResumeResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/resumes", tags=["resumes"])


# ── Master Resumes ──────────────────────────────────────────────────────

@router.post("/master", response_model=MasterResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_master_resume(
    body: MasterResumeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    resume = MasterResume(
        user_id=current_user.id,
        title=body.title,
        content=body.content,
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("/master", response_model=list[MasterResumeResponse])
async def list_master_resumes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MasterResume)
        .where(MasterResume.user_id == current_user.id)
        .order_by(MasterResume.created_at.desc())
    )
    return result.scalars().all()


@router.get("/master/{resume_id}", response_model=MasterResumeResponse)
async def get_master_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master resume not found")
    return resume


# ── Tailored Resumes ────────────────────────────────────────────────────

@router.post("/tailor", response_model=TailoredResumeResponse, status_code=status.HTTP_201_CREATED)
async def tailor_resume(
    body: TailorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Validate master resume ownership
    mr_result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == body.master_resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    master = mr_result.scalar_one_or_none()
    if master is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master resume not found")

    # Validate job description ownership
    jd_result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == body.job_description_id,
            JobDescription.user_id == current_user.id,
        )
    )
    job = jd_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    # Run the AI tailoring pipeline
    from app.agents.orchestrator import run_tailoring_pipeline

    pipeline_result = await run_tailoring_pipeline(
        master_resume=master.content,
        jd_text=job.raw_text,
        user_rulebook=current_user.rulebook,
        company_name=job.company_name,
    )

    tailored = TailoredResume(
        user_id=current_user.id,
        master_resume_id=master.id,
        job_description_id=job.id,
        content=pipeline_result.get("final_draft", master.content),
        qa_status="pass" if pipeline_result.get("qa_passed") else "fail",
        qa_score=pipeline_result.get("confidence_score", 0),
        confidence_scores=pipeline_result.get("qa_result", {}),
    )
    db.add(tailored)
    await db.flush()
    await db.refresh(tailored)
    return tailored


@router.get("/tailored", response_model=list[TailoredResumeResponse])
async def list_tailored_resumes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(TailoredResume)
        .where(TailoredResume.user_id == current_user.id)
        .order_by(TailoredResume.created_at.desc())
    )
    return result.scalars().all()


@router.get("/tailored/{resume_id}", response_model=TailoredResumeResponse)
async def get_tailored_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(TailoredResume).where(
            TailoredResume.id == resume_id,
            TailoredResume.user_id == current_user.id,
        )
    )
    tailored = result.scalar_one_or_none()
    if tailored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tailored resume not found")
    return tailored


@router.get("/tailored/{resume_id}/pdf")
async def download_tailored_pdf(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(TailoredResume).where(
            TailoredResume.id == resume_id,
            TailoredResume.user_id == current_user.id,
        )
    )
    tailored = result.scalar_one_or_none()
    if tailored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tailored resume not found")

    from app.services.pdf_service import render_resume_pdf

    user_name = current_user.full_name
    pdf_bytes = render_resume_pdf(tailored.content, user_name)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{resume_id}.pdf"'},
    )
