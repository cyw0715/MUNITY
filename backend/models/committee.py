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
    document_types = Column(JSON, default=list)  # 文件类型完整列表（内置 + 自定义）
    # 同 motion_types_configured：区分「从未配置」与「配置后删空」
    document_types_configured = Column(Boolean, default=False, nullable=False)
    # 侧边栏品牌：徽标文字（1–2 字符，可为 emoji）、上传的图标文件名、标题
    logo_icon = Column(String(16), nullable=True)
    logo_image = Column(String(255), nullable=True)
    display_title = Column(String(100), nullable=True)
    # 主发言名单的单位时长（秒）。主发言名单不依附动议，拿不到动议里的
    # unit_duration，因此时长按会场单独保存，可在计时器抬头栏直接调整。
    main_unit_duration = Column(Integer, default=60)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    staff_members = relationship("User", back_populates="committee", foreign_keys="User.committee_id")
    delegations = relationship("Delegation", back_populates="committee")
    agenda_items = relationship("AgendaItem", back_populates="committee")
    motions = relationship("Motion", back_populates="committee")
    timeline = relationship("Timeline", back_populates="committee", uselist=False)
