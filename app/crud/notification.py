from sqlalchemy.orm import Session
from app.db import models

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    claim_id: int | None = None,
) -> models.Notification:
    notif = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        claim_id=claim_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_user_notifications(db: Session, user_id: int, limit: int = 50):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def mark_notification_read(db: Session, notification_id: int, user_id: int):
    notif = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id, models.Notification.user_id == user_id)
        .first()
    )
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_notifications_read(db: Session, user_id: int):
    db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
