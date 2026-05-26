from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class Delegation(Base):
    __tablename__ = "delegations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    committee = relationship("Committee", back_populates="delegations")
    members = relationship("User", back_populates="delegation", foreign_keys="User.delegation_id")
