from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db import models
from fastapi import HTTPException


def _calculate_days_ago(dt: datetime | None, now: datetime) -> int:
    if not dt:
        return 0
    if dt.tzinfo is None and now.tzinfo is not None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def get_all_groups(db: Session):
    return db.query(models.Group).all()


def assign_mentor_to_group(db: Session, group_id: int, mentor_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group / Vertical not found.")

    mentor = db.query(models.User).filter(
        models.User.id == mentor_id,
        models.User.role.in_([models.UserRole.MENTOR, models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN]),
    ).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found or user is not a mentor/admin.")

    if mentor not in group.mentors:
        group.mentors.append(mentor)
        db.commit()

    return group.mentors


def remove_mentor_from_group(db: Session, group_id: int, mentor_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group / Vertical not found.")

    mentor = db.query(models.User).filter(models.User.id == mentor_id).first()
    if mentor and mentor in group.mentors:
        group.mentors.remove(mentor)
        db.commit()

    return group.mentors


def get_group_mentors(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group / Vertical not found.")
    return group.mentors


def get_mentor_claim_queue(db: Session, group_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.group_id == group_id)
        .filter(models.Claim.status == models.ClaimStatus.PENDING_REVIEW)
        .order_by(models.Claim.submitted_at.asc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.name,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": _calculate_days_ago(c.submitted_at, now),
        }
        for c in claims
    ]


def get_mentor_all_assigned_queue(db: Session, mentor_id: int):
    """
    Returns pending review claims across all verticals assigned to this mentor.
    """
    mentor = db.query(models.User).filter(models.User.id == mentor_id).first()
    if not mentor:
        return []

    assigned_group_ids = [g.id for g in mentor.assigned_verticals]

    query = db.query(models.Claim).filter(
        models.Claim.status == models.ClaimStatus.PENDING_REVIEW
    )
    if assigned_group_ids:
        query = query.filter(models.Claim.group_id.in_(assigned_group_ids))

    claims = query.order_by(models.Claim.submitted_at.asc()).all()
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.name,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": _calculate_days_ago(c.submitted_at, now),
        }
        for c in claims
    ]


def get_admin_claim_queue(db: Session, group_id: int | None = None):
    query = (
        db.query(models.Claim)
        .filter(models.Claim.status == models.ClaimStatus.DISPUTED)
    )
    if group_id:
        query = query.filter(models.Claim.group_id == group_id)

    claims = query.order_by(models.Claim.submitted_at.asc()).all()
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.name,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": _calculate_days_ago(c.submitted_at, now),
        }
        for c in claims
    ]


def get_mentee_claims(db: Session, user_id: int, group_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.submitter_id == user_id)
        .filter(models.Claim.group_id == group_id)
        .order_by(models.Claim.submitted_at.desc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.name,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": _calculate_days_ago(c.submitted_at, now),
        }
        for c in claims
    ]