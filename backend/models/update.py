from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from database import Base


class Update(Base):
    __tablename__ = "updates"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String(20), default="text")  # text / file
    file_path = Column(String(500), nullable=True)
    visibility = Column(JSON, default=list)  # 可见代表ID列表，空=全部可见
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
