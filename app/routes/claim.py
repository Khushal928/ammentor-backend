from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db import models
from app.crud.auth import get_current_user
from app.schemas.claim import ClaimDetailOut

router = APIRouter()

@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim_details(
    claim_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    is_owner = claim.submitter_id == current_user.id
    is_reviewer = current_user.role in (models.UserRole.MENTOR, models.UserRole.ADMIN)

    if not is_owner and not is_reviewer:
        raise HTTPException(status_code=403, detail="Not authorized to view this claim.")

    team_members = (
        db.query(models.ClaimTeamMember)
        .filter(models.ClaimTeamMember.claim_id == claim_id)
        .all()
    )

    history = (
        db.query(models.ClaimStatusHistory)
        .filter(models.ClaimStatusHistory.claim_id == claim_id)
        .order_by(models.ClaimStatusHistory.changed_at.asc())
        .all()
    )

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
        "submitted_at": claim.submitted_at,
        "approved_at": claim.approved_at,
        "submitter": {
            "user_id": claim.submitter.id,
            "username": claim.submitter.username,
            "email": claim.submitter.email,
        },
        "evaluated_by_mentor": (
            {
                "user_id": claim.evaluated_by_mentor.id,
                "username": claim.evaluated_by_mentor.username,
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
            for member in team_members
        ],
        "history": [
            {
                "old_status": h.old_status,
                "new_status": h.new_status,
                "comment": h.comment,
                "changed_by_id": h.changed_by_id,
                "changed_at": h.changed_at,
            }
            for h in history
        ],
        # "evidence":
    }



