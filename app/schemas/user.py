from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.db.models import ClaimStatus

class UserClaimOut(BaseModel):
    id: int
    group_id: int
    event_name: str
    status: ClaimStatus
    days_ago: int

    class Config:
        from_attributes = True

class UserProfileOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    roll_number: Optional[str] = None
    department: Optional[str] = None
    vertical_id: Optional[int] = None
    vertical_title: Optional[str] = None

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[str] = None
    department: Optional[str] = None
    vertical_id: Optional[int] = None