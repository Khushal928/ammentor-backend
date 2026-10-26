from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.db import get_db
from app.db import models
from app.crud.auth import get_current_user
from app.crud.user import get_all_user_claims
from app.schemas.user import UserClaimOut, UserProfileOut, UserProfileUpdate

router = APIRouter()


@router.get("/me", response_model=UserProfileOut)
def get_my_details(
    current_user: models.User = Depends(get_current_user),
):
    """
    Get profile details of the authenticated student / mentor / admin.
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "roll_number": current_user.roll_number,
        "department": current_user.department,
        "vertical_id": current_user.vertical_id,
        "vertical_title": current_user.vertical.title if current_user.vertical else None,
    }


@router.patch("/me", response_model=UserProfileOut)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update profile attributes (name, roll_number, department, vertical_id).
    """
    if payload.name is not None:
        current_user.name = payload.name
    if payload.roll_number is not None:
        current_user.roll_number = payload.roll_number
    if payload.department is not None:
        current_user.department = payload.department
    if payload.vertical_id is not None:
        group = db.query(models.Group).filter(models.Group.id == payload.vertical_id).first()
        if not group:
            raise HTTPException(status_code=400, detail="Invalid vertical_id.")
        current_user.vertical_id = payload.vertical_id

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "roll_number": current_user.roll_number,
        "department": current_user.department,
        "vertical_id": current_user.vertical_id,
        "vertical_title": current_user.vertical.title if current_user.vertical else None,
    }


@router.get("/me/claims", response_model=List[UserClaimOut])
def get_my_claims(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all claims submitted by the current user sorted by status priority.
    """
    return get_all_user_claims(db, user_id=current_user.id)
