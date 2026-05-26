from sqlalchemy import Column, Integer, DateTime, ForeignKey
from datetime import datetime, timezone
from database import Base


class SpeechRecord(Base):
    __tablename__ = "speech_records"

    id = Column(Integer, primary_key=True, index=True)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    motion_id = Column(Integer, ForeignKey("motions.id"), nullable=True)
    duration = Column(Integer, default=0)  # 发言时长（秒）
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
