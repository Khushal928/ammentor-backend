from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from app.db import models


def _apply_time_period_filter(query, time_period: str | None):
    now = datetime.now(timezone.utc)
    if time_period == "month":
        start_date = now - timedelta(days=30)
        return query.filter(models.Claim.submitted_at >= start_date)
    elif time_period == "semester":
        # Approximate a 6-month semester window
        start_date = now - timedelta(days=180)
        return query.filter(models.Claim.submitted_at >= start_date)
    elif time_period == "academic_year":
        # 1-year window
        start_date = now - timedelta(days=365)
        return query.filter(models.Claim.submitted_at >= start_date)
    return query


def get_overall_leaderboard(
    db: Session,
    time_period: str = "all_time",
    group_id: int | None = None,
    department: str | None = None,
    event_level: models.EventLevel | None = None,
    participation_category: models.ParticipationCategory | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Public overall leaderboard ranking students by total points from approved claims.
    Tie-breaking: points DESC, count of position-holder claims DESC, earliest submission ASC.
    """
    query = (
        db.query(
            models.User.id.label("student_id"),
            models.User.name.label("student_name"),
            models.User.department.label("department"),
            models.Group.title.label("vertical_title"),
            func.coalesce(func.sum(models.Claim.points), 0).label("total_points"),
            func.count(models.Claim.id).label("approved_claims_count"),
            func.sum(
                case(
                    (models.Claim.participation_category == models.ParticipationCategory.POSITION_HOLDER, 1),
                    else_=0,
                )
            ).label("position_holder_count"),
            func.min(models.Claim.submitted_at).label("first_submission"),
        )
        .join(models.Claim, models.Claim.submitter_id == models.User.id)
        .outerjoin(models.Group, models.Claim.group_id == models.Group.id)
        .filter(models.Claim.status == models.ClaimStatus.APPROVED_PUBLISHED)
    )

    query = _apply_time_period_filter(query, time_period)

    if group_id:
        query = query.filter(models.Claim.group_id == group_id)
    if department:
        query = query.filter(models.User.department.ilike(f"%{department}%"))
    if event_level:
        query = query.filter(models.Claim.event_level == event_level)
    if participation_category:
        query = query.filter(models.Claim.participation_category == participation_category)

    query = query.group_by(
        models.User.id,
        models.User.name,
        models.User.department,
        models.Group.title,
    ).order_by(
        desc("total_points"),
        desc("position_holder_count"),
        "first_submission",
    )

    results = query.offset(offset).limit(limit).all()

    leaderboard = []
    for rank, r in enumerate(results, start=offset + 1):
        leaderboard.append({
            "rank": rank,
            "student_id": r.student_id,
            "student_name": r.student_name,
            "department": r.department,
            "vertical_title": r.vertical_title,
            "total_points": int(r.total_points),
            "approved_claims_count": int(r.approved_claims_count),
        })

    return leaderboard


def get_vertical_leaderboard(
    db: Session,
    time_period: str = "all_time",
):
    """
    Vertical-wise leaderboard comparing aggregate points across MITHRA verticals.
    """
    query = (
        db.query(
            models.Group.id.label("group_id"),
            models.Group.title.label("title"),
            models.Group.description.label("description"),
            func.coalesce(func.sum(models.Claim.points), 0).label("total_points"),
            func.count(models.Claim.id).label("approved_claims_count"),
            func.count(func.distinct(models.Claim.submitter_id)).label("student_count"),
        )
        .outerjoin(
            models.Claim,
            (models.Claim.group_id == models.Group.id) &
            (models.Claim.status == models.ClaimStatus.APPROVED_PUBLISHED)
        )
    )

    query = _apply_time_period_filter(query, time_period)

    results = query.group_by(
        models.Group.id,
        models.Group.title,
        models.Group.description,
    ).order_by(desc("total_points")).all()

    return [
        {
            "rank": rank,
            "vertical_id": r.group_id,
            "vertical_title": r.title,
            "description": r.description,
            "total_points": int(r.total_points),
            "approved_claims_count": int(r.approved_claims_count),
            "student_count": int(r.student_count),
        }
        for rank, r in enumerate(results, start=1)
    ]


def get_department_leaderboard(
    db: Session,
    time_period: str = "all_time",
):
    """
    Department-wise leaderboard ranking departments by total points.
    """
    query = (
        db.query(
            models.User.department.label("department"),
            func.coalesce(func.sum(models.Claim.points), 0).label("total_points"),
            func.count(models.Claim.id).label("approved_claims_count"),
            func.count(func.distinct(models.User.id)).label("student_count"),
        )
        .join(models.Claim, models.Claim.submitter_id == models.User.id)
        .filter(models.Claim.status == models.ClaimStatus.APPROVED_PUBLISHED)
        .filter(models.User.department.isnot(None))
    )

    query = _apply_time_period_filter(query, time_period)

    results = query.group_by(models.User.department).order_by(desc("total_points")).all()

    return [
        {
            "rank": rank,
            "department": r.department,
            "total_points": int(r.total_points),
            "approved_claims_count": int(r.approved_claims_count),
            "student_count": int(r.student_count),
        }
        for rank, r in enumerate(results, start=1)
    ]


def get_student_public_profile(db: Session, student_id: int):
    """
    Public student profile view showing achievement timeline and points.
    """
    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student:
        return None

    approved_claims = (
        db.query(models.Claim)
        .filter(
            models.Claim.submitter_id == student_id,
            models.Claim.status == models.ClaimStatus.APPROVED_PUBLISHED,
        )
        .order_by(models.Claim.approved_at.desc())
        .all()
    )

    total_points = sum(c.points or 0 for c in approved_claims)
    claim_count = len(approved_claims)

    # Calculate badges / milestones per Section 8
    badges = []
    if claim_count >= 1:
        badges.append({"id": "first_claim", "name": "Trailblazer", "description": "First verified achievement"})
    if claim_count >= 5:
        badges.append({"id": "five_claims", "name": "High Achiever", "description": "5+ verified achievements"})
    if claim_count >= 10:
        badges.append({"id": "ten_claims", "name": "Campus Champion", "description": "10+ verified achievements"})
    if any(c.participation_category == models.ParticipationCategory.POSITION_HOLDER for c in approved_claims):
        badges.append({"id": "podium_finisher", "name": "Podium Finisher", "description": "1st/2nd/3rd place placement"})
    if any(c.event_level in (models.EventLevel.NATIONAL, models.EventLevel.INTERNATIONAL) for c in approved_claims):
        badges.append({"id": "national_rep", "name": "National/Global Honor", "description": "National or International achievement"})

    timeline = [
        {
            "claim_id": c.id,
            "event_name": c.event_name,
            "event_level": c.event_level,
            "participation_category": c.participation_category,
            "event_start_date": c.event_start_date,
            "event_end_date": c.event_end_date,
            "organising_body": c.organising_body,
            "points": c.points,
            "supporting_link": c.supporting_link,
            "approved_at": c.approved_at,
            "vertical": c.group.title if c.group else None,
        }
        for c in approved_claims
    ]

    return {
        "student_id": student.id,
        "student_name": student.name,
        "department": student.department,
        "roll_number": student.roll_number,
        "vertical": student.vertical.title if student.vertical else None,
        "total_points": total_points,
        "approved_claims_count": claim_count,
        "badges": badges,
        "timeline": timeline,
    }
