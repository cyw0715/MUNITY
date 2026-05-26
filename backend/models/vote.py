from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    title = Column(String(200), nullable=False)  # 投票主题
    rule = Column(String(50), default="qualified_majority")  # qualified_majority / simple_majority / custom
    custom_rule = Column(JSON, nullable=True)  # 自定义规则配置
    status = Column(String(20), default="pending")  # pending / voting / passed / failed
    veto_enabled = Column(Boolean, default=False)  # 是否启用一票否决权
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    # 关系
    records = relationship("VoteRecord", back_populates="vote", cascade="all, delete-orphan")


class VoteRecord(Base):
    __tablename__ = "vote_records"

    id = Column(Integer, primary_key=True, index=True)
    vote_id = Column(Integer, ForeignKey("votes.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    choice = Column(String(20), nullable=True)  # yes / no / abstain / null(未投票)
    has_veto = Column(Boolean, default=False)  # 是否拥有一票否决权
    is_observer = Column(Boolean, default=False)  # 是否为观察员
    can_vote = Column(Boolean, default=True)  # 是否可以投票
    voted_at = Column(DateTime, nullable=True)

    # 关系
    vote = relationship("Vote", back_populates="records")
