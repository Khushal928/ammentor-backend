from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Date, ForeignKey, UniqueConstraint, Enum, Table, func
from sqlalchemy.orm import relationship
from app.db.db import Base
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    MENTOR = "mentor"
    PROGRAM_ADMIN = "program_admin"
    SUPER_ADMIN = "super_admin"

class EventLevel(str, enum.Enum):
    SCHOOL_DEPARTMENT = "school_department"
    CAMPUS = "campus"
    INTER_CAMPUS = "inter_campus"
    STATE = "state"
    NATIONAL = "national"
    INTERNATIONAL = "international"

class ParticipationCategory(str, enum.Enum):
    PARTICIPANT = "participant"
    POSITION_HOLDER = "position_holder"
    ORGANISER_LEAD = "organiser_lead"
    VOLUNTEER_CORE_TEAM = "volunteer_core_team"
    REPRESENTATIVE = "representative"

class ClaimStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    NEEDS_INFO = "needs_info"
    APPROVED_PUBLISHED = "approved_published"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"

VALID_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
    ClaimStatus.DRAFT:               {ClaimStatus.PENDING_REVIEW, ClaimStatus.WITHDRAWN},
    ClaimStatus.PENDING_REVIEW:      {ClaimStatus.NEEDS_INFO, ClaimStatus.APPROVED_PUBLISHED, ClaimStatus.REJECTED, ClaimStatus.WITHDRAWN},
    ClaimStatus.NEEDS_INFO:          {ClaimStatus.PENDING_REVIEW, ClaimStatus.WITHDRAWN},
    ClaimStatus.REJECTED:            {ClaimStatus.DISPUTED, ClaimStatus.CLOSED},
    ClaimStatus.DISPUTED:            {ClaimStatus.APPROVED_PUBLISHED, ClaimStatus.REJECTED, ClaimStatus.CLOSED},
    ClaimStatus.APPROVED_PUBLISHED:  set(),
    ClaimStatus.CLOSED:              set(),
    ClaimStatus.WITHDRAWN:           set(),
}

mentor_verticals = Table(
    "mentor_verticals",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    roll_number = Column(String, nullable=True, index=True)
    department = Column(String, nullable=True, index=True)
    vertical_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    vertical = relationship("Group", foreign_keys=[vertical_id], lazy="joined")
    assigned_verticals = relationship("Group", secondary=mentor_verticals, back_populates="mentors")
    
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    mentors = relationship("User", secondary=mentor_verticals, back_populates="assigned_verticals")

class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, index=True)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    event_name=Column(String, nullable=False)
    event_level=Column(Enum(EventLevel), nullable=False)
    participation_category=Column(Enum(ParticipationCategory), nullable=False)
    event_start_date=Column(Date, nullable=False)
    event_end_date=Column(Date, nullable=False)
    organising_body=Column(String, nullable=False)
    description=Column(String, nullable=True)
    # evidence= TODO
    team=Column(Boolean, nullable=False, default=False)
    supporting_link = Column(String, nullable=True) 
    status = Column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.PENDING_REVIEW)
    mentor_feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    info_request = Column(Text, nullable=True)
    points = Column(Integer, nullable=True)
    evaluated_by_mentor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitter = relationship("User", foreign_keys=[submitter_id], lazy="joined")
    evaluated_by_mentor = relationship("User", foreign_keys=[evaluated_by_mentor_id], lazy="joined")
    group = relationship("Group", foreign_keys=[group_id], lazy="joined")
    evidence_files = relationship("ClaimEvidence", back_populates="claim", cascade="all, delete-orphan", lazy="selectin")
    team_members = relationship("ClaimTeamMember", cascade="all, delete-orphan", lazy="selectin")

class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    claim = relationship("Claim", back_populates="evidence_files")

class ClaimTeamMember(Base):
    __tablename__ = "claim_team_members"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    roll_number = Column(String, nullable=False)
    name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("claim_id", "roll_number", name="uq_claim_roll_number"),
    )


class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"
    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)   
    old_status = Column(Enum(ClaimStatus), nullable=True)
    new_status = Column(Enum(ClaimStatus), nullable=False)
    comment = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    claim = relationship("Claim", foreign_keys=[claim_id])


class OTP(Base):
    __tablename__ = "otp"

    email = Column(String, primary_key=True, index=True)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class ClaimRubric(Base):
    __tablename__ = "claim_rubrics"
    id = Column(Integer, primary_key=True)
    event_level = Column(Enum(EventLevel), nullable=False)
    participation_category = Column(Enum(ParticipationCategory), nullable=False)
    points = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("event_level", "participation_category", name="uq_rubric_level_category"),
    )