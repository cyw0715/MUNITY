from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    features = Column(JSON, default=list)  # 可用功能列表
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    staff_members = relationship("User", back_populates="committee", foreign_keys="User.committee_id")
    delegations = relationship("Delegation", back_populates="committee")
    agenda_items = relationship("AgendaItem", back_populates="committee")
    motions = relationship("Motion", back_populates="committee")
    timeline = relationship("Timeline", back_populates="committee", uselist=False)
