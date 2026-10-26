import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.claim import (
    ClaimCreate,
    ClaimDetailOut,
    ClaimInfoRequest,
    ClaimRejectRequest,
    ClaimDisputeRequest,
    ClaimResolveDisputeRequest,
    ClaimUpdate,
    EvidenceOut,
)
from app.crud.auth import get_current_user
from app.crud.claim import transition_claim, create_claim as crud_create_claim
from app.db.db import get_db
from app.db import models

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per Section 6
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _serialize_claim(claim: models.Claim) -> dict:
    """Helper to cleanly serialize Claim ORM instance to ClaimDetailOut."""
    return {
        "claim_id": claim.id,
        "event_name": claim.event_name,
        "event_level": claim.event_level,
        "participation_category": claim.participation_category,
        "event_start_date": claim.event_start_date,
        "event_end_date": claim.event_end_date,
        "organising_body": claim.organising_body,
        "description": claim.description,
        "team": claim.team,
        "supporting_link": claim.supporting_link,
        "status": claim.status,
        "mentor_feedback": claim.mentor_feedback,
        "rejection_reason": claim.rejection_reason,
        "info_request": claim.info_request,
        "points": claim.points,
        "submitted_at": claim.submitted_at,
        "approved_at": claim.approved_at,
        "submitter": {
            "id": claim.submitter.id,
            "name": claim.submitter.name,
            "email": claim.submitter.email,
        },
        "evaluated_by_mentor": (
            {
                "id": claim.evaluated_by_mentor.id,
                "name": claim.evaluated_by_mentor.name,
                "email": claim.evaluated_by_mentor.email,
            }
            if claim.evaluated_by_mentor
            else None
        ),
        "group": {
            "group_id": claim.group.id,
            "title": claim.group.title,
        },
        "team_members": [
            {
                "roll_number": member.roll_number,
                "name": member.name,
            }
            for member in (claim.team_members or [])
        ],
        "evidence_files": [
            {
                "id": ev.id,
                "file_name": ev.file_name,
                "file_url": ev.file_url,
                "file_type": ev.file_type,
                "uploaded_at": ev.uploaded_at,
            }
            for ev in (claim.evidence_files or [])
        ],
        "history": [
            {
                "old_status": h.old_status,
                "new_status": h.new_status,
                "comment": h.comment,
                "changed_by_id": h.changed_by_id,
                "changed_at": h.changed_at,
            }
            for h in (claim.status_history if hasattr(claim, "status_history") else [])
        ],
    }


@router.post("/create_claim", response_model=ClaimDetailOut)
def create_claim_endpoint(
    claim: ClaimCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new achievement claim or save as draft.
    Authenticated student only. Submit status defaults to PENDING_REVIEW.
    """
    new_claim = crud_create_claim(
        db=db,
        submitter_id=current_user.id,
        group_id=claim.group_id,
        event_name=claim.event_name,
        event_level=claim.event_level,
        participation_category=claim.participation_category,
        event_start_date=claim.event_start_date,
        event_end_date=claim.event_end_date,
        organising_body=claim.organising_body,
        description=claim.description,
        supporting_link=claim.supporting_link,
        team=claim.team,
        status=claim.status,
        submitted_at=claim.submitted_at,
    )

    history = (
        db.query(models.ClaimStatusHistory)
        .filter(models.ClaimStatusHistory.claim_id == new_claim.id)
        .order_by(models.ClaimStatusHistory.changed_at.asc())
        .all()
    )
    new_claim.status_history = history
    return _serialize_claim(new_claim)


@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim_details(
    claim_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get full details for a claim.
    Authorized for claim submitter, assigned vertical mentors, and Program/Super Admins.
    """
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    is_owner = claim.submitter_id == current_user.id
    is_admin = current_user.role in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN)
    is_mentor = current_user.role == models.UserRole.MENTOR

    if not is_owner and not is_admin and not is_mentor:
        raise HTTPException(status_code=403, detail="Not authorized to view this claim.")

    history = (
        db.query(models.ClaimStatusHistory)
        .filter(models.ClaimStatusHistory.claim_id == claim_id)
        .order_by(models.ClaimStatusHistory.changed_at.asc())
        .all()
    )
    claim.status_history = history
    return _serialize_claim(claim)


@router.patch("/{claim_id}", response_model=ClaimDetailOut)
def update_claim_endpoint(
    claim_id: int,
    payload: ClaimUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Edit claim details while in DRAFT, PENDING_REVIEW, or NEEDS_INFO state (Claim submitter only).
    """
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own claims.")

    if claim.status not in (models.ClaimStatus.DRAFT, models.ClaimStatus.PENDING_REVIEW, models.ClaimStatus.NEEDS_INFO):
        raise HTTPException(
            status_code=400,
            detail=f"Claims in '{claim.status.value}' status cannot be edited.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)

    db.commit()
    db.refresh(claim)

    history = (
        db.query(models.ClaimStatusHistory)
        .filter(models.ClaimStatusHistory.claim_id == claim_id)
        .order_by(models.ClaimStatusHistory.changed_at.asc())
        .all()
    )
    claim.status_history = history
    return _serialize_claim(claim)


@router.post("/{claim_id}/resubmit", response_model=ClaimDetailOut)
def resubmit_claim_endpoint(
    claim_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resubmit a claim that was in NEEDS_INFO or DRAFT state back to PENDING_REVIEW.
    """
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only resubmit your own claims.")

    res = transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.PENDING_REVIEW,
        changed_by_id=current_user.id,
        comment="Student resubmitted claim with requested details.",
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/approve", response_model=ClaimDetailOut)
@router.post("/claim/{claim_id}/approve", response_model=ClaimDetailOut)
def approve_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mentor approves claim.
    Automatically scores and publishes the claim per Section 5 (Auto-publish confirmed).
    """
    if current_user.role not in (models.UserRole.MENTOR, models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only mentors and admins can approve claims.")

    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.APPROVED_PUBLISHED,
        changed_by_id=current_user.id,
        comment="Approved by mentor.",
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/reject", response_model=ClaimDetailOut)
@router.post("/claim/{claim_id}/reject", response_model=ClaimDetailOut)
def reject_claim(
    claim_id: int,
    request: ClaimRejectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mentor rejects claim with mandatory reason.
    """
    if current_user.role not in (models.UserRole.MENTOR, models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only mentors and admins can reject claims.")

    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.REJECTED,
        changed_by_id=current_user.id,
        reason=request.reason,
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/needs-info", response_model=ClaimDetailOut)
@router.post("/claim/{claim_id}/needs-info", response_model=ClaimDetailOut)
def needs_info(
    claim_id: int,
    request: ClaimInfoRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mentor requests more information from the student.
    """
    if current_user.role not in (models.UserRole.MENTOR, models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only mentors and admins can request information.")

    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.NEEDS_INFO,
        changed_by_id=current_user.id,
        reason=request.message,
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/withdraw", response_model=ClaimDetailOut)
@router.post("/claim/{claim_id}/withdraw", response_model=ClaimDetailOut)
def withdraw_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Student withdraws their own pending claim.
    """
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only withdraw your own claims.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.WITHDRAWN,
        changed_by_id=current_user.id,
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/dispute", response_model=ClaimDetailOut)
def dispute_claim_endpoint(
    claim_id: int,
    request: ClaimDisputeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Student raises a dispute/appeal on a rejected claim per Section 5.
    Escalates the claim for Program Admin review.
    """
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only dispute your own claims.")

    if claim.status != models.ClaimStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Only rejected claims can be disputed.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=models.ClaimStatus.DISPUTED,
        changed_by_id=current_user.id,
        reason=request.reason,
        comment=f"Dispute appeal: {request.reason}",
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/resolve-dispute", response_model=ClaimDetailOut)
def resolve_dispute_endpoint(
    claim_id: int,
    request: ClaimResolveDisputeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Program Admin / Super Admin reviews and resolves a disputed claim.
    Decision: 'approve' (auto-publishes points) or 'reject' (closes claim).
    """
    if current_user.role not in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Program Admins can resolve disputes.")

    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.status != models.ClaimStatus.DISPUTED:
        raise HTTPException(status_code=400, detail="Claim is not currently under dispute.")

    if request.decision.lower() == "approve":
        transition_claim(
            db=db,
            claim=claim,
            new_status=models.ClaimStatus.APPROVED_PUBLISHED,
            changed_by_id=current_user.id,
            comment=f"Admin dispute resolution: Approved. {request.comment or ''}".strip(),
        )
    elif request.decision.lower() == "reject":
        transition_claim(
            db=db,
            claim=claim,
            new_status=models.ClaimStatus.CLOSED,
            changed_by_id=current_user.id,
            comment=f"Admin dispute resolution: Rejected/Closed. {request.comment or ''}".strip(),
        )
    else:
        raise HTTPException(status_code=400, detail="Decision must be either 'approve' or 'reject'.")

    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)


@router.post("/{claim_id}/evidence", response_model=EvidenceOut)
def upload_claim_evidence(
    claim_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload supporting evidence file (certificate, photo, official result) per Section 6.
    Allowed: PDF, JPG, PNG, WEBP (up to 10MB).
    """
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if claim.submitter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the claim submitter can upload evidence.")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 10MB.")

    safe_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest_path = UPLOAD_DIR / safe_filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/claim/evidence/file/{safe_filename}"
    evidence = models.ClaimEvidence(
        claim_id=claim_id,
        file_name=file.filename or safe_filename,
        file_url=file_url,
        file_type=file.content_type,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.get("/evidence/file/{file_key}")
def download_evidence_file(
    file_key: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Secure file access for evidence.
    Data privacy per Section 11: Only assigned mentors, submitter, and admins see supporting files.
    """
    file_path = UPLOAD_DIR / file_key
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Evidence file not found.")

    evidence = db.query(models.ClaimEvidence).filter(
        models.ClaimEvidence.file_url.endswith(file_key)
    ).first()

    if evidence and evidence.claim:
        is_owner = evidence.claim.submitter_id == current_user.id
        is_admin = current_user.role in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN)
        is_mentor = current_user.role == models.UserRole.MENTOR
        if not is_owner and not is_admin and not is_mentor:
            raise HTTPException(status_code=403, detail="Not authorized to view this evidence file.")

    return FileResponse(path=file_path, filename=evidence.file_name if evidence else file_key)


@router.post("/claims/{claim_id}/transition", response_model=ClaimDetailOut)
def transition_claim_endpoint(
    claim_id: int,
    new_status: models.ClaimStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mentor transitions claim status directly.
    """
    if current_user.role not in (models.UserRole.MENTOR, models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only mentors and admins can change claim status.")

    claim = db.get(models.Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")

    transition_claim(
        db=db,
        claim=claim,
        new_status=new_status,
        changed_by_id=current_user.id,
    )
    return get_claim_details(claim_id=claim_id, current_user=current_user, db=db)
