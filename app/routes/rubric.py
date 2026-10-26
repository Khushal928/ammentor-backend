from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db import models
from app.crud.auth import get_current_user
from app.crud.rubric import get_all_rubric_items, upsert_rubric_item, seed_default_rubric
from app.schemas.rubric import RubricItemOut, RubricItemUpdate, RubricMatrixOut

router = APIRouter()


@router.get("", response_model=List[RubricItemOut])
def get_rubric_items(db: Session = Depends(get_db)):
    """
    Get all scoring rubric entries.
    """
    return get_all_rubric_items(db)


@router.get("/matrix", response_model=RubricMatrixOut)
def get_rubric_matrix(db: Session = Depends(get_db)):
    """
    Get scoring rubric formatted as a 2D matrix (Level x Category).
    """
    items = get_all_rubric_items(db)
    levels = [e.value for e in models.EventLevel]
    categories = [p.value for p in models.ParticipationCategory]

    matrix: dict[str, dict[str, int]] = {cat: {lvl: 0 for lvl in levels} for cat in categories}
    for item in items:
        matrix[item.participation_category.value][item.event_level.value] = item.points

    return {
        "levels": levels,
        "categories": categories,
        "matrix": matrix,
    }


@router.put("", response_model=RubricItemOut)
def update_rubric_item(
    payload: RubricItemUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update or create a scoring rubric rule (Program Admin / Super Admin only).
    """
    if current_user.role not in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Program Admins can edit the point rubric.")

    return upsert_rubric_item(
        db=db,
        event_level=payload.event_level,
        participation_category=payload.participation_category,
        points=payload.points,
    )


@router.post("/seed", response_model=dict)
def seed_rubric(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Seed default rubric values from Section 7 of briefing document (Admin only).
    """
    if current_user.role not in (models.UserRole.PROGRAM_ADMIN, models.UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Only Program Admins can seed the point rubric.")

    count = seed_default_rubric(db)
    return {"message": f"Successfully seeded {count} default rubric rules."}
