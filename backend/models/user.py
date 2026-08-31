from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

# 学团-委员会 关联表
staff_committee_association = Table(
    'staff_committees', Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('staff_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('committee_id', Integer, ForeignKey('committees.id'), nullable=False),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    extend_existing=True
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)  # admin / staff / delegate
    seat = Column(String(100), nullable=True)  # 代表席位（仅代表角色）
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=True)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    is_leader = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    committee = relationship("Committee", back_populates="staff_members", foreign_keys=[committee_id])
    delegation = relationship("Delegation", back_populates="members", foreign_keys=[delegation_id])
    staff_committees_rel = relationship("Committee", secondary="staff_committees",
                                        primaryjoin="User.id==staff_committees.c.staff_id",
                                        secondaryjoin="staff_committees.c.committee_id==Committee.id",
                                        backref="assigned_staff", viewonly=True)
