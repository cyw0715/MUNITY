from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from datetime import datetime, timezone
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    drafter = Column(String(100), nullable=False)
    doc_type = Column(String(30), nullable=False)  # declaration / memorandum / agreement
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    signing_countries = Column(JSON, nullable=True)  # 签署国家列表（协定专用）
    secrecy = Column(String(20), default="public")  # public / secret（协定专用）
    published = Column(Boolean, default=False)  # 是否已发布
    recalled = Column(Boolean, default=False)  # 是否已撤回
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
