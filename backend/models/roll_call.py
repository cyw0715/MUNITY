from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone
from database import Base


class RollCall(Base):
    __tablename__ = "roll_calls"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    delegate_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可选，精确到代表
    is_present = Column(Boolean, default=False)  # 出席/未出席
    session_id = Column(Integer, default=1)  # 第几次点名
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
