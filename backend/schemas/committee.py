from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CommitteeBase(BaseModel):
    name: str


class CommitteeCreate(CommitteeBase):
    features: List[str] = []


class CommitteeOut(CommitteeBase):
    id: int
    features: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class CommitteeUpdate(BaseModel):
    name: Optional[str] = None
    features: Optional[List[str]] = None
