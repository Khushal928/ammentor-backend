from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.db.models import EventLevel, ParticipationCategory


class LeaderboardEntryOut(BaseModel):
    rank: int
    student_id: int
    student_name: str
    department: Optional[str] = None
    vertical_title: Optional[str] = None
    total_points: int
    approved_claims_count: int


class VerticalLeaderboardEntryOut(BaseModel):
    rank: int
    vertical_id: int
    vertical_title: str
    description: Optional[str] = None
    total_points: int
    approved_claims_count: int
    student_count: int


class DepartmentLeaderboardEntryOut(BaseModel):
    rank: int
    department: str
    total_points: int
    approved_claims_count: int
    student_count: int


class StudentBadgeOut(BaseModel):
    id: str
    name: str
    description: str


class StudentTimelineItemOut(BaseModel):
    claim_id: int
    event_name: str
    event_level: EventLevel
    participation_category: ParticipationCategory
    event_start_date: date
    event_end_date: date
    organising_body: str
    points: Optional[int] = None
    supporting_link: Optional[str] = None
    approved_at: Optional[datetime] = None
    vertical: Optional[str] = None


class StudentPublicProfileOut(BaseModel):
    student_id: int
    student_name: str
    department: Optional[str] = None
    roll_number: Optional[str] = None
    vertical: Optional[str] = None
    total_points: int
    approved_claims_count: int
    badges: List[StudentBadgeOut] = []
    timeline: List[StudentTimelineItemOut] = []
