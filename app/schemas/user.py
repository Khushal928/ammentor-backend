from pydantic import BaseModel
from app.db.models import ClaimStatus

class UserClaimOut(BaseModel):
    id: int
    group_id: int
    event_name: str
    status: ClaimStatus
    days_ago: int

    class Config:
        from_attributes = True