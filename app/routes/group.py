from app.crud.group import get_mentee_claims, get_mentor_claim_queue, get_admin_claim_queue
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.db import models
from app.schemas.group import GroupCreate, GroupOut, GroupUpdate
from app.crud.auth import get_current_user
from app.db.models import UserRole

router = APIRouter()
@router.post("/create", response_model=GroupOut)
def create_new_group(
    group_data: GroupCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create groups.")

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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update groups.")

    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


@router.get("/{group_id}/claims")
def get_group_claims(
    group_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found.")

    if current_user.role == UserRole.MENTOR:
        return get_mentor_claim_queue(db, group_id=group_id)
    if current_user.role == UserRole.ADMIN:
        return get_admin_claim_queue(db, group_id=group_id)
    else:
        return get_mentee_claims(db, user_id=current_user.id, group_id=group_id)
