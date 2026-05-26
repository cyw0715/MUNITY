from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DelegationBase(BaseModel):
    name: str


class DelegationCreate(DelegationBase):
    committee_id: int


class DelegationOut(BaseModel):
    id: int
    name: str
    committee_id: int
    created_at: datetime

    class Config:
        from_attributes = True
