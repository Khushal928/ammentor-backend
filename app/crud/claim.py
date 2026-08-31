from http.client import HTTPException
from sqlalchemy.orm import Session
from db import models
from datetime import datetime, date


def create_claim(
    db: Session,
    submitter_id: int,
    group_id: int,
    event_name: str,
    event_level: models.EventLevel,
    participation_category: models.ParticipationCategory,
    event_start_date: date,
    event_end_date: date,
    organising_body: str,
    team: bool,
    status: models.ClaimStatus,
    submitted_at: datetime,
):
    claim = models.Claim(
        submitter_id=submitter_id,
        group_id=group_id,
        event_name=event_name,
        event_level=event_level,
        participation_category=participation_category,
        event_start_date=event_start_date,
        event_end_date=event_end_date,
        organising_body=organising_body,
        team=team,
        status=status,
        submitted_at=submitted_at,
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return claim


def transition_claim(
    db: Session,
    claim: models.Claim,
    new_status: models.ClaimStatus,
    reason: str | None = None,
):
    current_status = claim.status

    if new_status not in models.VALID_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition claim from "
                   f"{current_status} to {new_status}",
        )

    if new_status == models.ClaimStatus.REJECTED:
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required",
            )

        claim.rejection_reason = reason

    if new_status == models.ClaimStatus.APPROVED_PUBLISHED:
        claim.points = calculate_claim_points(db, claim)

    claim.status = new_status

    db.commit()
    db.refresh(claim)

    return claim


def calculate_claim_points(
    db: Session,
    claim: models.Claim,
) -> int:
    rubric = (db.query(models.ClaimRubric).filter(models.ClaimRubric.event_level == claim.event_level,models.ClaimRubric.participation_category== claim.participation_category).first())

    if rubric is None:
        raise HTTPException(
            status_code=400,
            detail="No scoring rubric found for this event level and participation category",
        )

    return rubric.points