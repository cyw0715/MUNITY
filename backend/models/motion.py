from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class Motion(Base):
    __tablename__ = "motions"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    type = Column(String(30), nullable=False)
    topic = Column(String(200), nullable=True)
    unit_duration = Column(Integer, nullable=True)
    total_duration = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")
    proposer_delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    proposer_delegate_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    committee = relationship("Committee")
    speakers = relationship("SpeakerEntry", back_populates="motion")


class SpeakerEntry(Base):
    __tablename__ = "speakers_entries"

    id = Column(Integer, primary_key=True, index=True)
    motion_id = Column(Integer, ForeignKey("motions.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    delegate_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order = Column(Integer, default=0)
    has_spoken = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    content = Column(Text, nullable=True)  # 发言内容记录
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    motion = relationship("Motion", back_populates="speakers")
    delegation = relationship("Delegation")
    delegate = relationship("User")
