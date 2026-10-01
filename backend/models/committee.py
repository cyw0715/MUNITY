from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    features = Column(JSON, default=list)  # 可用功能列表
    motion_types = Column(JSON, default=list)  # 动议类型完整列表（内置 + 自定义）
    # 是否已配置过动议类型。用于区分「从未配置」（展示内置默认）
    # 与「配置后删空」（保持为空）——后者删掉全部内置类型也应生效。
    motion_types_configured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    staff_members = relationship("User", back_populates="committee", foreign_keys="User.committee_id")
    delegations = relationship("Delegation", back_populates="committee")
    agenda_items = relationship("AgendaItem", back_populates="committee")
    motions = relationship("Motion", back_populates="committee")
    timeline = relationship("Timeline", back_populates="committee", uselist=False)
