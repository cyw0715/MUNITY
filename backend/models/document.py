from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from datetime import datetime, timezone
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    drafter = Column(String(100), nullable=False)
    doc_type = Column(String(30), nullable=False)  # 文件类型：内置用 key(declaration/…)，自定义用类型名
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    departments = Column(JSON, nullable=True)  # 涉及部门列表（按文件类型配置决定是否启用）
    file_path = Column(String(500), nullable=True)
    signing_countries = Column(JSON, nullable=True)  # 签署国家列表（协定专用）
    secrecy = Column(String(20), default="public")  # public / secret（协定专用）
    published = Column(Boolean, default=False)  # 是否已发布
    recalled = Column(Boolean, default=False)  # 是否已撤回
    endorsing_delegations = Column(JSON, nullable=True)  # 联署代表团ID列表
    endorsement_data = Column(JSON, nullable=True)  # { del_id: {status: "pending"|"approved"|"rejected", note: "", updated_at: ""} }
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
