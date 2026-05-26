from sqlalchemy import Column, Integer, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date, timezone
from database import Base


class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), unique=True, nullable=False)
    
    # 会议内当前日期（公元年月日）
    conference_date = Column(Date, nullable=True)
    
    # 流速：多少现实小时 = 1个会议天
    hours_per_day = Column(Float, default=1.0)
    
    # 上次更新时的现实时间戳（用于计算当前会议日期）
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    committee = relationship("Committee", back_populates="timeline")
