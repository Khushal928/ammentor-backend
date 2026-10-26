from sqlalchemy.orm import Session
from app.db import models

# Configured default rubric values from Section 7 of briefing document
DEFAULT_RUBRIC_VALUES: dict[tuple[models.EventLevel, models.ParticipationCategory], int] = {
    # Participant
    (models.EventLevel.SCHOOL_DEPARTMENT, models.ParticipationCategory.PARTICIPANT): 2,
    (models.EventLevel.CAMPUS, models.ParticipationCategory.PARTICIPANT): 4,
    (models.EventLevel.INTER_CAMPUS, models.ParticipationCategory.PARTICIPANT): 6,
    (models.EventLevel.STATE, models.ParticipationCategory.PARTICIPANT): 8,
    (models.EventLevel.NATIONAL, models.ParticipationCategory.PARTICIPANT): 12,
    (models.EventLevel.INTERNATIONAL, models.ParticipationCategory.PARTICIPANT): 18,

    # Volunteer / Core Team
    (models.EventLevel.SCHOOL_DEPARTMENT, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 3,
    (models.EventLevel.CAMPUS, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 6,
    (models.EventLevel.INTER_CAMPUS, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 9,
    (models.EventLevel.STATE, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 12,
    (models.EventLevel.NATIONAL, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 16,
    (models.EventLevel.INTERNATIONAL, models.ParticipationCategory.VOLUNTEER_CORE_TEAM): 22,

    # Organiser / Lead
    (models.EventLevel.SCHOOL_DEPARTMENT, models.ParticipationCategory.ORGANISER_LEAD): 5,
    (models.EventLevel.CAMPUS, models.ParticipationCategory.ORGANISER_LEAD): 8,
    (models.EventLevel.INTER_CAMPUS, models.ParticipationCategory.ORGANISER_LEAD): 12,
    (models.EventLevel.STATE, models.ParticipationCategory.ORGANISER_LEAD): 16,
    (models.EventLevel.NATIONAL, models.ParticipationCategory.ORGANISER_LEAD): 20,
    (models.EventLevel.INTERNATIONAL, models.ParticipationCategory.ORGANISER_LEAD): 28,

    # Position Holder
    (models.EventLevel.SCHOOL_DEPARTMENT, models.ParticipationCategory.POSITION_HOLDER): 6,
    (models.EventLevel.CAMPUS, models.ParticipationCategory.POSITION_HOLDER): 10,
    (models.EventLevel.INTER_CAMPUS, models.ParticipationCategory.POSITION_HOLDER): 15,
    (models.EventLevel.STATE, models.ParticipationCategory.POSITION_HOLDER): 20,
    (models.EventLevel.NATIONAL, models.ParticipationCategory.POSITION_HOLDER): 28,
    (models.EventLevel.INTERNATIONAL, models.ParticipationCategory.POSITION_HOLDER): 40,

    # Representative
    (models.EventLevel.SCHOOL_DEPARTMENT, models.ParticipationCategory.REPRESENTATIVE): 0,
    (models.EventLevel.CAMPUS, models.ParticipationCategory.REPRESENTATIVE): 5,
    (models.EventLevel.INTER_CAMPUS, models.ParticipationCategory.REPRESENTATIVE): 8,
    (models.EventLevel.STATE, models.ParticipationCategory.REPRESENTATIVE): 12,
    (models.EventLevel.NATIONAL, models.ParticipationCategory.REPRESENTATIVE): 18,
    (models.EventLevel.INTERNATIONAL, models.ParticipationCategory.REPRESENTATIVE): 26,
}


def seed_default_rubric(db: Session) -> int:
    """Seeds the rubric table with default values if not already present."""
    seeded_count = 0
    for (level, category), pts in DEFAULT_RUBRIC_VALUES.items():
        existing = (
            db.query(models.ClaimRubric)
            .filter(
                models.ClaimRubric.event_level == level,
                models.ClaimRubric.participation_category == category,
            )
            .first()
        )
        if not existing:
            rubric_item = models.ClaimRubric(
                event_level=level,
                participation_category=category,
                points=pts,
            )
            db.add(rubric_item)
            seeded_count += 1

    if seeded_count > 0:
        db.commit()
    return seeded_count


def get_all_rubric_items(db: Session):
    return db.query(models.ClaimRubric).order_by(
        models.ClaimRubric.event_level,
        models.ClaimRubric.participation_category,
    ).all()


def upsert_rubric_item(
    db: Session,
    event_level: models.EventLevel,
    participation_category: models.ParticipationCategory,
    points: int,
) -> models.ClaimRubric:
    item = (
        db.query(models.ClaimRubric)
        .filter(
            models.ClaimRubric.event_level == event_level,
            models.ClaimRubric.participation_category == participation_category,
        )
        .first()
    )
    if item:
        item.points = points
    else:
        item = models.ClaimRubric(
            event_level=event_level,
            participation_category=participation_category,
            points=points,
        )
        db.add(item)
    db.commit()
    db.refresh(item)
    return item
