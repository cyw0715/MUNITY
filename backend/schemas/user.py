from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    role: str  # admin / staff / delegate


class UserCreate(UserBase):
    password: str
    committee_id: Optional[int] = None
    delegation_id: Optional[int] = None
    is_leader: bool = False


class UserOut(UserBase):
    id: int
    committee_id: Optional[int] = None
    delegation_id: Optional[int] = None
    seat: Optional[str] = None
    is_leader: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
