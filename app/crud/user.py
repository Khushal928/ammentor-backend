from datetime import datetime, timedelta, timezone
from app.db import models
from sqlalchemy.orm import Session
from app.db.models import ClaimStatus



def get_all_user_claims(db: Session, user_id: int):
    claims = (
        db.query(models.Claim)
        .filter(models.Claim.submitter_id == user_id)
        .all()
    )

    claims.sort(key=lambda c: ClaimStatus.index(c.status))

    now = datetime.now(timezone.utc)
    for c in claims:
        c.days_ago = (now - c.submitted_at).days

    return claims
