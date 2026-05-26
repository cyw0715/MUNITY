from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from database import Base


class Directive(Base):
    __tablename__ = "directives"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    drafter = Column(String(100), nullable=False)
    admin_points = Column(Integer, default=0)
    secrecy = Column(String(20), default="public")  # public / secret
    content = Column(Text, nullable=True)
    departments = Column(JSON, nullable=True)  # 涉及部门列表
    status = Column(String(20), default="unread")  # unread / no_simulate / pending_simulate / simulated
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
