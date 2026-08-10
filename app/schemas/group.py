from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class GroupCreate(BaseModel):
    title: str
    description: Optional[str] = None

class GroupOut(BaseModel):
    id: int
    title: str
    description: Optional[str]

    class Config:
        from_attributes = True

class ClaimQueueItem(BaseModel):
    claim_id: int
    username: str
    user_id: int
    event_name: str
    days_ago: int

class GroupUpdate(BaseModel):
    title: str | None = None
    description: str | None = None