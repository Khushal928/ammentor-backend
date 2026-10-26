from datetime import datetime, timezone
from app.db import models
from sqlalchemy.orm import Session
from app.db.models import ClaimStatus


# Explicit display ordering: lower number = shown first
_STATUS_ORDER = {s: i for i, s in enumerate(ClaimStatus)}


def _calculate_days_ago(dt: datetime | None, now: datetime) -> int:
    if not dt:
        return 0
    if dt.tzinfo is None and now.tzinfo is not None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def get_all_user_claims(db: Session, user_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.submitter_id == user_id)
        .all()
    )

    claims.sort(key=lambda c: _STATUS_ORDER.get(c.status, 999))

    now = datetime.now(timezone.utc)
    for c in claims:
        c.days_ago = _calculate_days_ago(c.submitted_at, now)

    return claims
