from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

from app.db.models import EventLevel, ParticipationCategory, ClaimStatus


class UserBrief(BaseModel):
    user_id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class TeamMemberOut(BaseModel):
    roll_number: str
    name: str

    class Config:
        from_attributes = True

class GroupBrief(BaseModel):
    group_id: int
    title: str

    class Config:
        from_attributes = True

class ClaimHistoryOut(BaseModel):
    old_status: Optional[ClaimStatus] = None
    new_status: ClaimStatus
    comment: Optional[str] = None
    changed_by_id: int
    changed_at: datetime

    class Config:
        from_attributes = True


class ClaimDetailOut(BaseModel):
    claim_id: int
    event_name: str
    event_level: EventLevel
    participation_category: ParticipationCategory
    event_start_date: date
    event_end_date: date
    organising_body: str
    description: Optional[str] = None
    team: bool
    supporting_link: Optional[str] = None
    status: ClaimStatus
    mentor_feedback: Optional[str] = None
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    group: GroupBrief
    submitter: UserBrief
    evaluated_by_mentor: Optional[UserBrief] = None
    team_members: List[TeamMemberOut] = []
    history: List[ClaimHistoryOut] = []
    # evidence: List[EvidenceOut] = []  # once evidence/attachments model exists

    class Config:
        from_attributes = True