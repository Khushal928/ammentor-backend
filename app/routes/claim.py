from schemas.claim import ClaimDetailOut,ClaimInfoRequest,ClaimRejectRequest
from crud.claim import transition_claim,create_claim
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from db.db import get_db
from db import models
from crud.auth import get_current_user

router = APIRouter()

@router.post("/create_claim", response_model=ClaimDetailOut)
def create_claim(
    claim: models.ClaimCreate,
    db: Session = Depends(get_db),
):
    return create_claim(
        db=db,
        submitter_id=claim.submitter_id,
        group_id=claim.group_id,
        event_name=claim.event_name,
        event_level=claim.event_level,
        participation_category=claim.participation_category,
        event_start_date=claim.event_start_date,
        event_end_date=claim.event_end_date,
        organising_body=claim.organising_body,
        team=claim.team,
        status=claim.status,
        submitted_at=claim.submitted_at,
    )


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

    #TODO remove the db query here

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




# all possible transisiions of a claim could be defined here

@router.post(
    "/claim/{claim_id}/approve",
    response_model=ClaimDetailOut,
)
def approve_claim(claim_id: int,db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.MENTOR:
        raise HTTPException(
            status_code=403,
            detail="Only mentors can approve claims",
        )

    claim = db.get(models.Claim, claim_id)

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return transition_claim(
        db,
        claim,
        models.ClaimStatus.APPROVED_PUBLISHED,
    )

@router.post("/claim/{claim_id}/reject",response_model=ClaimDetailOut,)
def reject_claim(
    claim_id: int,
    request: ClaimRejectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != models.UserRole.MENTOR:
        raise HTTPException(
            status_code=403,
            detail="Only mentors can reject claims",
        )

    claim = db.get(models.Claim, claim_id)

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return transition_claim(
        db,
        claim,
        models.ClaimStatus.REJECTED,
        request.reason,
    )

@router.post( "/claim/{claim_id}/needs-info",response_model=ClaimDetailOut)
def needs_info(
    claim_id: int,
    request: ClaimInfoRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != models.UserRole.MENTOR:
        raise HTTPException(
            status_code=403,
            detail="Only mentors can request information",
        )

    claim = db.get(models.Claim, claim_id)

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    claim.info_request = request.message

    return transition_claim(
        db,
        claim,
        models.ClaimStatus.NEEDS_INFO,
    )

@router.post(
    "/claim/{claim_id}/withdraw",
    response_model=ClaimDetailOut,
)
def withdraw_claim(claim_id: int,db: Session = Depends(get_db),current_user: models.User = Depends(get_current_user)):
    claim = db.get(models.Claim, claim_id)

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    if claim.submitter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only withdraw your own claims",
        )

    return transition_claim(
        db,
        claim,
        models.ClaimStatus.WITHDRAWN,
    )

@router.post("/claims/{claim_id}/transition",response_model=ClaimDetailOut)
def transition_claim_endpoint(
    claim_id: int,
    new_status: models.ClaimStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != models.UserRole.MENTOR:
        raise HTTPException(
            status_code=403,
            detail="Only mentors can change claim status",
        )

    claim = db.get(models.Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim not found",
        )

    return transition_claim(db, claim, new_status)

