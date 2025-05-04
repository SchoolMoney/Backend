from typing import Optional

from pydantic import BaseModel, ConfigDict
from datetime import date as datetime_date


class ChildCreate(BaseModel):
    """Model for creating a new child"""

    name: str
    surname: str
    birth_date: datetime_date
    group_id: int | None = None
    group_access_code: str | None = None

    model_config = ConfigDict(extra="forbid")


class ChildUpdate(BaseModel):
    """Model for updating a child - all fields optional"""

    name: Optional[str] = None
    surname: Optional[str] = None
    birth_date: Optional[datetime_date] = None
    group_id: Optional[int] = None
    group_access_code: str | None = None

    model_config = ConfigDict(extra="forbid")


class ChildBatchUpdate(BaseModel):
    """Model for batch updating children - requires ID"""

    id: int
    name: Optional[str] = None
    surname: Optional[str] = None
    birth_date: Optional[datetime_date] = None
    group_id: Optional[int] = None
    group_access_code: str | None = None

    model_config = ConfigDict(extra="forbid")
