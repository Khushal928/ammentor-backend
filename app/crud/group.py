from datetime import datetime, timedelta, timezone
from app.db import models
from sqlalchemy.orm import Session



def get_mentor_claim_queue(db: Session, group_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.group_id == group_id)
        .filter(models.Claim.status == models.ClaimStatus.PENDING)
        .order_by(models.Claim.submitted_at.asc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.username,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": (now - c.submitted_at).days,
        }
        for c in claims
    ]

def get_admin_claim_queue(db: Session, group_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.group_id == group_id)
        .filter(models.Claim.status == models.ClaimStatus.DISPUTED)
        .order_by(models.Claim.submitted_at.asc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return [
        {
            "claim_id": c.id,
            "username": c.submitter.username,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": (now - c.submitted_at).days,
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
            "username": c.submitter.username,
            "user_id": c.submitter_id,
            "event_name": c.event_name,
            "days_ago": (now - c.submitted_at).days,
        }
        for c in claims
    ]