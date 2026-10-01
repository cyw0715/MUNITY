from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CommitteeBase(BaseModel):
    name: str


class CommitteeCreate(CommitteeBase):
    features: List[str] = []
    # 创建时也允许一并设置品牌，否则前端传来的值会被静默丢弃
    logo_icon: Optional[str] = None
    display_title: Optional[str] = None


class CommitteeOut(CommitteeBase):
    id: int
    features: List[str] = []
    logo_icon: Optional[str] = None
    logo_image: Optional[str] = None
    display_title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CommitteeUpdate(BaseModel):
    name: Optional[str] = None
    features: Optional[List[str]] = None
    logo_icon: Optional[str] = None
    display_title: Optional[str] = None
