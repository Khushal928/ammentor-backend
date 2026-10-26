from pydantic import BaseModel, ConfigDict
from app.db.models import EventLevel, ParticipationCategory

class RubricItemOut(BaseModel):
    id: int
    event_level: EventLevel
    participation_category: ParticipationCategory
    points: int

    model_config = ConfigDict(from_attributes=True)


class RubricItemUpdate(BaseModel):
    event_level: EventLevel
    participation_category: ParticipationCategory
    points: int


class RubricMatrixOut(BaseModel):
    levels: list[str]
    categories: list[str]
    matrix: dict[str, dict[str, int]]
