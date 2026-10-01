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
from services import hash_password, require_role, validate_password_strength

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

    validate_password_strength(user_data.password)
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

    # 同时写入 staff_committees 关联表（如果指定了委员会）
    if user_data.committee_id:
        from sqlalchemy import text
        ins = text("INSERT OR IGNORE INTO staff_committees (staff_id, committee_id) VALUES (:sid, :cid)")
        db.execute(ins, {"sid": staff.id, "cid": user_data.committee_id})
        db.commit()

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

    # 删除投票（先删投票记录，再删投票，避免遗留孤儿数据）
    from models.vote import Vote, VoteRecord
    vote_ids = [v.id for v in db.query(Vote).filter(Vote.committee_id == committee_id).all()]
    if vote_ids:
        db.query(VoteRecord).filter(VoteRecord.vote_id.in_(vote_ids)).delete(synchronize_session=False)
        db.query(Vote).filter(Vote.id.in_(vote_ids)).delete(synchronize_session=False)

    # 删除非对称消息
    from models.async_message import AsyncMessage
    db.query(AsyncMessage).filter(AsyncMessage.committee_id == committee_id).delete()

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

    # 清理 staff_committees 关联表。
    # 必须复用请求会话：此时会话已因前面的 DELETE 开启写事务并持有 SQLite 写锁，
    # 另开 engine.connect() 去写会在 commit 时抢 EXCLUSIVE 锁失败（database is locked）。
    from sqlalchemy import text
    db.execute(text("DELETE FROM staff_committees WHERE committee_id = :cid"), {"cid": committee_id})

    # 删除时间线
    db.query(Timeline).filter(Timeline.committee_id == committee_id).delete()

    # 删除委员会
    db.delete(committee)
    db.commit()
    return {"message": "删除成功"}


# ==================== 分配学团到委员会 ====================

class StaffCommitteeAssign(BaseModel):
    committee_ids: List[int]  # 可分配多个委员会


@router.put("/staff/{staff_id}/assign-committees")
def assign_staff_to_committees(
    staff_id: int,
    data: StaffCommitteeAssign,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """为学团分配多个委员会"""
    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()
    if not staff:
        raise HTTPException(status_code=404, detail="学团不存在")
    
    # 验证所有委员会存在
    committees = db.query(Committee).filter(Committee.id.in_(data.committee_ids)).all()
    found_ids = {c.id for c in committees}
    for cid in data.committee_ids:
        if cid not in found_ids:
            raise HTTPException(status_code=404, detail=f"委员会不存在 (id={cid})")
    
    # 先清空旧关联（复用请求会话，避免与自身写事务争抢 SQLite 写锁）
    from sqlalchemy import text
    db.execute(text("DELETE FROM staff_committees WHERE staff_id = :sid"), {"sid": staff_id})

    # 插入新关联
    if data.committee_ids:
        ins = text("INSERT OR IGNORE INTO staff_committees (staff_id, committee_id) VALUES (:sid, :cid)")
        for cid in data.committee_ids:
            db.execute(ins, {"sid": staff_id, "cid": cid})

    # 也更新 committee_id 字段为第一个委员会（兼容旧版）
    staff.committee_id = data.committee_ids[0] if data.committee_ids else None
    db.commit()
    return {"message": "分配成功", "committee_ids": data.committee_ids}


@router.get("/staff-committees")
def list_staff_committees(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """一次性返回「学团 -> 委员会」全量映射。

    前端学团管理页原本为每个学团并发请求一次 /staff/{id}/committees，
    学团数量超过连接池容量（默认 5+10）后请求会排队 30s 才报错，
    表现为页面卡死并连带拖垮其他管理员页面。改为单次聚合查询。
    """
    from sqlalchemy import text

    result: dict = {}

    rows = db.execute(text(
        "SELECT sc.staff_id, c.id, c.name FROM staff_committees sc "
        "JOIN committees c ON c.id = sc.committee_id "
        "JOIN users u ON u.id = sc.staff_id "
        "WHERE u.role = 'staff'"
    )).fetchall()
    for sid, cid, cname in rows:
        result.setdefault(int(sid), []).append({"id": int(cid), "name": cname})

    # 兼容旧版：仅有 committee_id 字段、未写入关联表的学团
    legacy = db.query(User).filter(User.role == "staff", User.committee_id.isnot(None)).all()
    need = [u for u in legacy if u.id not in result]
    if need:
        cmap = {c.id: c.name for c in db.query(Committee).all()}
        for u in need:
            if u.committee_id in cmap:
                result.setdefault(u.id, []).append({"id": u.committee_id, "name": cmap[u.committee_id]})

    return result


@router.get("/staff/{staff_id}/committees")
def get_staff_committees(
    staff_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """获取学团的委员会列表（复用请求会话，避免额外占用连接）"""
    from sqlalchemy import text

    rows = db.execute(
        text("SELECT c.id, c.name FROM committees c "
             "JOIN staff_committees sc ON c.id = sc.committee_id "
             "WHERE sc.staff_id = :sid"),
        {"sid": staff_id}
    ).fetchall()
    committees = [{"id": row[0], "name": row[1]} for row in rows]

    # 兼容旧版
    if not committees:
        staff = db.query(User).filter(User.id == staff_id).first()
        if staff and staff.committee_id:
            c = db.query(Committee).filter(Committee.id == staff.committee_id).first()
            if c:
                committees = [{"id": c.id, "name": c.name}]

    return committees


@router.put("/staff/{staff_id}/assign/{committee_id}")
def assign_staff_to_committee(
    staff_id: int,
    committee_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """单委员会分配（兼容旧版，保留已有关联）"""
    staff = db.query(User).filter(User.id == staff_id, User.role == "staff").first()
    if not staff:
        raise HTTPException(status_code=404, detail="学团不存在")
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="委员会不存在")
    
    # 复用请求会话写入关联表（避免第二条连接与自身写事务争抢写锁）
    from sqlalchemy import text
    ins = text("INSERT OR IGNORE INTO staff_committees (staff_id, committee_id) VALUES (:sid, :cid)")
    db.execute(ins, {"sid": staff_id, "cid": committee_id})

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
