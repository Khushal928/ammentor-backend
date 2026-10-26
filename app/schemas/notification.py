from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    claim_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
