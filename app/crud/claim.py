from datetime import datetime, date, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db import models
from app.crud.notification import create_notification


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
    status: models.ClaimStatus = models.ClaimStatus.PENDING_REVIEW,
    submitted_at: datetime | None = None,
    description: str | None = None,
    supporting_link: str | None = None,
) -> models.Claim:
    if submitted_at is None:
        submitted_at = datetime.now(timezone.utc)

    claim = models.Claim(
        submitter_id=submitter_id,
        group_id=group_id,
        event_name=event_name,
        event_level=event_level,
        participation_category=participation_category,
        event_start_date=event_start_date,
        event_end_date=event_end_date,
        organising_body=organising_body,
        description=description,
        supporting_link=supporting_link,
        team=team,
        status=status,
        submitted_at=submitted_at,
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    # Record initial status in audit history
    history = models.ClaimStatusHistory(
        claim_id=claim.id,
        changed_by_id=submitter_id,
        old_status=None,
        new_status=status,
        comment="Claim submitted" if status == models.ClaimStatus.PENDING_REVIEW else "Claim saved as draft",
        changed_at=submitted_at,
    )
    db.add(history)
    db.commit()

    # Notify vertical mentors when submitted for review
    if status == models.ClaimStatus.PENDING_REVIEW:
        group = db.query(models.Group).filter(models.Group.id == group_id).first()
        if group and group.mentors:
            for mentor in group.mentors:
                create_notification(
                    db=db,
                    user_id=mentor.id,
                    title="New Claim in Review Queue",
                    message=f"A new claim for '{event_name}' in {group.title} has been submitted for review.",
                    claim_id=claim.id,
                )

    return claim


def transition_claim(
    db: Session,
    claim: models.Claim,
    new_status: models.ClaimStatus,
    changed_by_id: int,
    reason: str | None = None,
    comment: str | None = None,
) -> models.Claim:
    current_status = claim.status

    if new_status not in models.VALID_TRANSITIONS.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition claim from {current_status.value} to {new_status.value}",
        )

    action_comment = comment or reason

    if new_status == models.ClaimStatus.REJECTED:
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required",
            )
        claim.rejection_reason = reason
        action_comment = reason
        create_notification(
            db=db,
            user_id=claim.submitter_id,
            title="Claim Rejected",
            message=f"Your claim for '{claim.event_name}' was rejected: {reason}",
            claim_id=claim.id,
        )

    elif new_status == models.ClaimStatus.NEEDS_INFO:
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=400,
                detail="Information request details are required",
            )
        claim.info_request = reason
        action_comment = reason
        create_notification(
            db=db,
            user_id=claim.submitter_id,
            title="Information Requested on Claim",
            message=f"Mentor requested additional details on '{claim.event_name}': {reason}",
            claim_id=claim.id,
        )

    elif new_status == models.ClaimStatus.APPROVED_PUBLISHED:
        claim.points = calculate_claim_points(db, claim)
        claim.approved_at = datetime.now(timezone.utc)
        claim.evaluated_by_mentor_id = changed_by_id
        create_notification(
            db=db,
            user_id=claim.submitter_id,
            title="Claim Approved & Published",
            message=f"Congratulations! Your claim for '{claim.event_name}' was approved ({claim.points} points awarded).",
            claim_id=claim.id,
        )

    elif new_status == models.ClaimStatus.DISPUTED:
        # Notify program admins about dispute escalation
        admins = db.query(models.User).filter(
            models.User.role.in_([models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN])
        ).all()
        for admin in admins:
            create_notification(
                db=db,
                user_id=admin.id,
                title="Claim Dispute Escalation",
                message=f"A dispute has been raised by student on claim #{claim.id} ('{claim.event_name}'): {reason or comment or 'No comment'}",
                claim_id=claim.id,
            )

    elif new_status == models.ClaimStatus.WITHDRAWN:
        action_comment = comment or "Withdrawn by student"

    claim.status = new_status

    # Record in audit trail
    history = models.ClaimStatusHistory(
        claim_id=claim.id,
        changed_by_id=changed_by_id,
        old_status=current_status,
        new_status=new_status,
        comment=action_comment,
    )
    db.add(history)

    db.commit()
    db.refresh(claim)

    return claim


def calculate_claim_points(
    db: Session,
    claim: models.Claim,
) -> int:
    rubric = (
        db.query(models.ClaimRubric)
        .filter(
            models.ClaimRubric.event_level == claim.event_level,
            models.ClaimRubric.participation_category == claim.participation_category,
        )
        .first()
    )

    if rubric is None:
        raise HTTPException(
            status_code=400,
            detail=f"No scoring rubric found for event level '{claim.event_level.value}' and category '{claim.participation_category.value}'",
        )

    return rubric.points