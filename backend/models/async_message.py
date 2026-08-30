from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class AsyncMessage(Base):
    """非对称消息（危机联动核心功能）"""
    __tablename__ = "async_messages"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 接收方式一：发给指定代表
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 接收方式二：发给指定代表团的全部成员
    receiver_delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    # public: 所有人可见, delegation: 仅本代表团可见, private: 仅指定代表可见
    visibility = Column(String(20), default="private")
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    committee = relationship("Committee")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    receiver_delegation = relationship("Delegation", foreign_keys=[receiver_delegation_id])
