from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.db import get_db
from app.db import models
from app.crud.auth import get_current_user
from app.crud.notification import (
    get_user_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)
from app.schemas.notification import NotificationOut

router = APIRouter()


@router.get("", response_model=List[NotificationOut])
def list_my_notifications(
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get in-app notifications for the authenticated user, newest first.
    """
    return get_user_notifications(db=db, user_id=current_user.id, limit=limit)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a single notification as read.
    """
    notif = mark_notification_read(db=db, notification_id=notification_id, user_id=current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notif


@router.post("/read-all", response_model=dict)
def read_all_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications for the authenticated user as read.
    """
    mark_all_notifications_read(db=db, user_id=current_user.id)
    return {"message": "All notifications marked as read."}
