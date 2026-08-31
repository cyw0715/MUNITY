from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
import json


class AsyncMessage(Base):
    """非对称消息（危机联动核心功能）"""
    __tablename__ = "async_messages"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 旧字段 — 保留以便反向兼容
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    receiver_delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    
    # 新字段 — JSON 数组，支持多接收者
    receiver_ids = Column(Text, default="[]")       # JSON: [1, 2, 3]
    receiver_delegation_ids = Column(Text, default="[]")  # JSON: [1, 2]
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    # public: 所有人可见, delegation: 仅指定代表团可见, private: 仅指定代表可见
    visibility = Column(String(20), default="private")
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # 多接收者的已读状态
    read_by = Column(Text, default="[]")  # JSON: [{"user_id": 1, "is_read": true, "read_at": "..."}]
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    committee = relationship("Committee")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    receiver_delegation = relationship("Delegation", foreign_keys=[receiver_delegation_id])


def get_receiver_ids(msg: AsyncMessage) -> list[int]:
    """获取消息的所有目标代表ID列表"""
    ids = set()
    try:
        if msg.receiver_ids and msg.receiver_ids != "[]":
            ids.update(json.loads(msg.receiver_ids))
    except Exception:
        pass
    # 兼容旧数据
    if msg.receiver_id and msg.receiver_id not in ids:
        ids.add(msg.receiver_id)
    return sorted(ids)


def get_receiver_delegation_ids(msg: AsyncMessage) -> list[int]:
    """获取消息的所有目标代表团ID列表"""
    ids = set()
    try:
        if msg.receiver_delegation_ids and msg.receiver_delegation_ids != "[]":
            ids.update(json.loads(msg.receiver_delegation_ids))
    except Exception:
        pass
    if msg.receiver_delegation_id and msg.receiver_delegation_id not in ids:
        ids.add(msg.receiver_delegation_id)
    return sorted(ids)


def is_message_visible_to(msg: AsyncMessage, user_id: int, delegation_id: int = None) -> bool:
    """判断消息是否对指定用户可见"""
    if msg.visibility == "public":
        return True
    if user_id in get_receiver_ids(msg):
        return True
    if delegation_id and msg.visibility == "delegation" and delegation_id in get_receiver_delegation_ids(msg):
        return True
    return False
