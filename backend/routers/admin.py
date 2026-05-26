from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.committee import Committee
from models.delegation import Delegation
from schemas.user import UserCreate, UserOut
from schemas.committee import CommitteeCreate, CommitteeOut, CommitteeUpdate
from schemas.delegation import DelegationCreate, DelegationOut
from services import hash_password, require_role

router = APIRouter(prefix="/api/admin", tags=["管理员"])


# ==================== 学团管理 ====================

@router.get("/staff", response_model=List[UserOut])
def list_staff(current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "staff").all()


@router.post("/staff", response_model=UserOut)
def create_staff(
    user_data: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    staff = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role="staff",
        created_by=current_user.id,
        committee_id=user_data.committee_id
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/staff/{staff_id}")
def delete_staff(
    staff_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()
    if not staff:
        raise HTTPException(status_code=404, detail="学团不存在")
    db.delete(staff)
    db.commit()
    return {"message": "删除成功"}


# ==================== 委员会管理 ====================

@router.get("/committees", response_model=List[CommitteeOut])
def list_committees(current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return db.query(Committee).all()


@router.post("/committees", response_model=CommitteeOut)
def create_committee(
    data: CommitteeCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    committee = Committee(name=data.name, features=data.features)
    db.add(committee)
    db.commit()
    db.refresh(committee)
    return committee


@router.put("/committees/{committee_id}", response_model=CommitteeOut)
def update_committee(
    committee_id: int,
    data: CommitteeUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="委员会不存在")
    if data.name is not None:
        committee.name = data.name
    if data.features is not None:
        committee.features = data.features
    db.commit()
    db.refresh(committee)
    return committee


class CommitteeCopy(BaseModel):
    name: str


@router.post("/committees/{committee_id}/copy", response_model=CommitteeOut)
def copy_committee(
    committee_id: int,
    data: CommitteeCopy,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """复制委员会（仅复制名称和功能配置）"""
    source = db.query(Committee).filter(Committee.id == committee_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="委员会不存在")

    new_committee = Committee(
        name=data.name,
        features=source.features.copy() if source.features else []
    )
    db.add(new_committee)
    db.commit()
    db.refresh(new_committee)
    return new_committee


@router.delete("/committees/{committee_id}")
def delete_committee(
    committee_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="委员会不存在")

    # 删除关联数据（按依赖顺序）
    from models import Delegation, User, Motion, SpeakerEntry, RollCall, AgendaItem, Directive, Document, Update, SpeechRecord
    from models.timeline import Timeline

    # 获取该委员会下的代表团
    delegation_ids = [d.id for d in db.query(Delegation).filter(Delegation.committee_id == committee_id).all()]

    # 删除发言记录
    db.query(SpeechRecord).filter(SpeechRecord.committee_id == committee_id).delete()
    # 删除局势更新
    db.query(Update).filter(Update.committee_id == committee_id).delete()
    # 删除文件
    db.query(Document).filter(Document.committee_id == committee_id).delete()
    # 删除指令
    db.query(Directive).filter(Directive.committee_id == committee_id).delete()
    # 删除议程
    db.query(AgendaItem).filter(AgendaItem.committee_id == committee_id).delete()
    # 删除点名
    db.query(RollCall).filter(RollCall.committee_id == committee_id).delete()

    # 删除发言名单和动议
    motions = db.query(Motion).filter(Motion.committee_id == committee_id).all()
    for m in motions:
        db.query(SpeakerEntry).filter(SpeakerEntry.motion_id == m.id).delete()
        db.delete(m)

    # 删除代表
    if delegation_ids:
        db.query(User).filter(User.role == "delegate", User.delegation_id.in_(delegation_ids)).delete()
        # 删除代表团
        db.query(Delegation).filter(Delegation.committee_id == committee_id).delete()

    # 取消学团与委员会的关联
    db.query(User).filter(User.role == "staff", User.committee_id == committee_id).update({"committee_id": None})

    # 删除时间线
    db.query(Timeline).filter(Timeline.committee_id == committee_id).delete()

    # 删除委员会
    db.delete(committee)
    db.commit()
    return {"message": "删除成功"}


# ==================== 分配学团到委员会 ====================

@router.put("/staff/{staff_id}/assign/{committee_id}")
def assign_staff_to_committee(
    staff_id: int,
    committee_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()
    if not staff:
        raise HTTPException(status_code=404, detail="学团不存在")
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="委员会不存在")
    staff.committee_id = committee_id
    db.commit()
    return {"message": "分配成功"}


# ==================== 获取当前用户信息 ====================

@router.get("/me")
def get_me(current_user: User = Depends(require_role("admin"))):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }
