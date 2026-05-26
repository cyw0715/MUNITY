from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)  # admin / staff / delegate
    seat = Column(String(100), nullable=True)  # 代表席位（仅代表角色）
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=True)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    is_leader = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    committee = relationship("Committee", back_populates="staff_members", foreign_keys=[committee_id])
    delegation = relationship("Delegation", back_populates="members", foreign_keys=[delegation_id])
