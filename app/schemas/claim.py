from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

from app.db.models import EventLevel, ParticipationCategory, ClaimStatus


class UserBrief(BaseModel):
    id: int
    name: str
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


class EvidenceOut(BaseModel):
    id: int
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    uploaded_at: datetime

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
    rejection_reason: Optional[str] = None
    info_request: Optional[str] = None
    points: Optional[int] = None
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    group: GroupBrief
    submitter: UserBrief
    evaluated_by_mentor: Optional[UserBrief] = None
    team_members: List[TeamMemberOut] = []
    evidence_files: List[EvidenceOut] = []
    history: List[ClaimHistoryOut] = []

    class Config:
        from_attributes = True

class ClaimRejectRequest(BaseModel):
    reason: str 


class ClaimInfoRequest(BaseModel):
    message: str


class ClaimDisputeRequest(BaseModel):
    reason: str


class ClaimResolveDisputeRequest(BaseModel):
    decision: str  # "approve" or "reject"
    comment: Optional[str] = None


class ClaimUpdate(BaseModel):
    event_name: Optional[str] = None
    event_level: Optional[EventLevel] = None
    participation_category: Optional[ParticipationCategory] = None
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    organising_body: Optional[str] = None
    description: Optional[str] = None
    team: Optional[bool] = None
    supporting_link: Optional[str] = None
    group_id: Optional[int] = None


class ClaimCreate(BaseModel):
    submitter_id: int | None = None
    group_id: int
    event_name: str
    event_level: EventLevel
    participation_category: ParticipationCategory
    event_start_date: date
    event_end_date: date
    organising_body: str
    description: Optional[str] = None
    supporting_link: Optional[str] = None
    team: bool = False
    status: ClaimStatus = ClaimStatus.PENDING_REVIEW
    submitted_at: datetime | None = None