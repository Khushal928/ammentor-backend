from typing import List
from app.crud.group import (
    get_all_groups,
    get_mentee_claims,
    get_mentor_claim_queue,
    get_admin_claim_queue,
    get_mentor_all_assigned_queue,
    assign_mentor_to_group,
    remove_mentor_from_group,
    get_group_mentors,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.db import models
from app.schemas.group import GroupCreate, GroupOut, GroupUpdate, MentorBrief, MentorAssignRequest
from app.crud.auth import get_current_user
from app.db.models import UserRole

router = APIRouter()


@router.get("", response_model=List[GroupOut])
def list_groups(db: Session = Depends(get_db)):
    """
    List all MITHRA verticals / groups.
    """
    return get_all_groups(db)


@router.post("/create", response_model=GroupOut)
def create_new_group(
    group_data: GroupCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new MITHRA vertical (Admin only).
    """
    if current_user.role not in (UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can create groups/verticals.")

    group = models.Group(title=group_data.title, description=group_data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.patch("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update MITHRA vertical details (Admin only).
    """
    if current_user.role not in (UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can update groups/verticals.")

    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


@router.post("/{group_id}/assign-mentor", response_model=List[MentorBrief])
def assign_mentor_endpoint(
    group_id: int,
    payload: MentorAssignRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Assign a mentor to a MITHRA vertical per Section 3 & 10 (Admin only).
    """
    if current_user.role not in (UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can assign mentors to verticals.")

    mentors = assign_mentor_to_group(db=db, group_id=group_id, mentor_id=payload.mentor_id)
    return mentors


@router.delete("/{group_id}/remove-mentor/{mentor_id}", response_model=List[MentorBrief])
def remove_mentor_endpoint(
    group_id: int,
    mentor_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove mentor assignment from a MITHRA vertical (Admin only).
    """
    if current_user.role not in (UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only admins can manage mentor assignments.")

    mentors = remove_mentor_from_group(db=db, group_id=group_id, mentor_id=mentor_id)
    return mentors


@router.get("/{group_id}/mentors", response_model=List[MentorBrief])
def get_vertical_mentors_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
):
    """
    List mentors assigned to a specific MITHRA vertical.
    """
    return get_group_mentors(db=db, group_id=group_id)


@router.get("/queue/pending")
def get_mentor_pending_queue(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mentor queue: returns pending claims auto-routed to verticals assigned to this mentor.
    """
    if current_user.role not in (UserRole.MENTOR, UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only mentors and admins can view review queues.")

    return get_mentor_all_assigned_queue(db=db, mentor_id=current_user.id)


@router.get("/{group_id}/claims")
def get_group_claims(
    group_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get claims for a specific vertical based on caller's role.
    """
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if current_user.role == UserRole.MENTOR:
        return get_mentor_claim_queue(db, group_id=group_id)
    if current_user.role in (UserRole.PROGRAM_ADMIN, UserRole.SUPER_ADMIN):
        return get_admin_claim_queue(db, group_id=group_id)
    else:
        return get_mentee_claims(db, user_id=current_user.id, group_id=group_id)
