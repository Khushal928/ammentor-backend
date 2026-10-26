from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db import models
from app.crud.leaderboard import (
    get_overall_leaderboard,
    get_vertical_leaderboard,
    get_department_leaderboard,
    get_student_public_profile,
)
from app.schemas.leaderboard import (
    LeaderboardEntryOut,
    VerticalLeaderboardEntryOut,
    DepartmentLeaderboardEntryOut,
    StudentPublicProfileOut,
)

router = APIRouter()


@router.get("/overall", response_model=List[LeaderboardEntryOut])
def overall_leaderboard(
    time_period: str = Query("all_time", regex="^(all_time|month|semester|academic_year)$"),
    group_id: Optional[int] = Query(None, description="Filter by MITHRA vertical"),
    department: Optional[str] = Query(None, description="Filter by student department"),
    event_level: Optional[models.EventLevel] = Query(None, description="Filter by event level"),
    participation_category: Optional[models.ParticipationCategory] = Query(None, description="Filter by role/category"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Public overall leaderboard view — ranks all students by approved achievement points.
    Accessible from outside campus network without login (read-only).
    """
    return get_overall_leaderboard(
        db=db,
        time_period=time_period,
        group_id=group_id,
        department=department,
        event_level=event_level,
        participation_category=participation_category,
        limit=limit,
        offset=offset,
    )


@router.get("/verticals", response_model=List[VerticalLeaderboardEntryOut])
def vertical_leaderboard(
    time_period: str = Query("all_time", regex="^(all_time|month|semester|academic_year)$"),
    db: Session = Depends(get_db),
):
    """
    Public vertical-wise leaderboard view — aggregates points across MITHRA verticals.
    """
    return get_vertical_leaderboard(db=db, time_period=time_period)


@router.get("/departments", response_model=List[DepartmentLeaderboardEntryOut])
def department_leaderboard(
    time_period: str = Query("all_time", regex="^(all_time|month|semester|academic_year)$"),
    db: Session = Depends(get_db),
):
    """
    Public department-wise leaderboard view.
    """
    return get_department_leaderboard(db=db, time_period=time_period)


@router.get("/student/{student_id}", response_model=StudentPublicProfileOut)
def student_public_profile(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    Public student achievement profile — verified achievements timeline, total points, and earned badges.
    """
    profile = get_student_public_profile(db=db, student_id=student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return profile
