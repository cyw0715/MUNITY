from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import os
import uuid
from database import get_db
from models.user import User
from models.committee import Committee
from models.delegation import Delegation
from models.agenda import AgendaItem
from models.motion import Motion, SpeakerEntry
from models.roll_call import RollCall
from models.speech_record import SpeechRecord
from models.directive import Directive
from models.document import Document
from models.update import Update
from schemas.user import UserOut
from schemas.delegation import DelegationBase, DelegationCreate, DelegationOut
from services import hash_password, require_role

router = APIRouter(prefix="/api/staff", tags=["学团"])


# 代表创建 schema（不需要 role，后端自动设为 delegate）
class DelegateCreate(BaseModel):
    username: str
    password: str
    seat: str
    delegation_id: Optional[int] = None
    is_leader: bool = False


def get_staff_committee(current_user: User) -> int:
    """获取学团所属委员会ID"""
    if not current_user.committee_id:
        raise HTTPException(status_code=400, detail="您尚未分配到任何委员会")
    return current_user.committee_id


# ==================== 代表管理 ====================

@router.get("/delegates", response_model=List[UserOut])
def list_delegates(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    # 获取该委员会下所有代表团的代表
    delegations = db.query(Delegation).filter(Delegation.committee_id == committee_id).all()
    delegation_ids = [d.id for d in delegations]

    # 查询：属于该委员会代表团的代表，或未分配代表团但由当前学团创建的代表
    query = db.query(User).filter(User.role == "delegate")
    if delegation_ids:
        query = query.filter(
            (User.delegation_id.in_(delegation_ids)) |
            (User.delegation_id.is_(None) & (User.created_by == current_user.id))
        )
    else:
        query = query.filter(
            User.delegation_id.is_(None) & (User.created_by == current_user.id)
        )
    return query.all()


@router.post("/delegates", response_model=UserOut)
def create_delegate(
    user_data: DelegateCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)

    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 如果指定了代表团，检查代表团是否属于当前委员会
    if user_data.delegation_id:
        delegation = db.query(Delegation).filter(
            Delegation.id == user_data.delegation_id,
            Delegation.committee_id == committee_id
        ).first()
        if not delegation:
            raise HTTPException(status_code=400, detail="代表团不存在或不属于当前委员会")

    delegate = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role="delegate",
        seat=user_data.seat,
        created_by=current_user.id,
        delegation_id=user_data.delegation_id,
        is_leader=user_data.is_leader
    )
    db.add(delegate)
    db.commit()
    db.refresh(delegate)
    return delegate


@router.put("/delegates/{delegate_id}/leader")
def set_delegate_leader(
    delegate_id: int,
    is_leader: bool = True,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    delegate = db.query(User).filter(User.id == delegate_id, User.role == "delegate").first()
    if not delegate:
        raise HTTPException(status_code=404, detail="代表不存在")
    # 验证代表属于当前委员会
    if delegate.delegation_id:
        delegation = db.query(Delegation).filter(
            Delegation.id == delegate.delegation_id,
            Delegation.committee_id == committee_id
        ).first()
        if not delegation:
            raise HTTPException(status_code=403, detail="无权操作此代表")
    delegate.is_leader = is_leader
    db.commit()
    return {"message": "设置成功"}


class SeatUpdate(BaseModel):
    seat: str


@router.put("/delegates/{delegate_id}/seat")
def update_delegate_seat(
    delegate_id: int,
    data: SeatUpdate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """修改代表席位"""
    committee_id = get_staff_committee(current_user)
    delegate = db.query(User).filter(User.id == delegate_id, User.role == "delegate").first()
    if not delegate:
        raise HTTPException(status_code=404, detail="代表不存在")
    # 验证代表属于当前委员会
    if delegate.delegation_id:
        delegation = db.query(Delegation).filter(
            Delegation.id == delegate.delegation_id,
            Delegation.committee_id == committee_id
        ).first()
        if not delegation:
            raise HTTPException(status_code=403, detail="无权操作此代表")
    delegate.seat = data.seat
    db.commit()
    return {"message": "修改成功"}


@router.delete("/delegates/{delegate_id}")
def delete_delegate(
    delegate_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    delegate = db.query(User).filter(User.id == delegate_id, User.role == "delegate").first()
    if not delegate:
        raise HTTPException(status_code=404, detail="代表不存在")
    db.delete(delegate)
    db.commit()
    return {"message": "删除成功"}


@router.put("/delegates/{delegate_id}/assign/{delegation_id}")
def assign_delegate_to_delegation(
    delegate_id: int,
    delegation_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    delegate = db.query(User).filter(User.id == delegate_id, User.role == "delegate").first()
    if not delegate:
        raise HTTPException(status_code=404, detail="代表不存在")
    delegation = db.query(Delegation).filter(
        Delegation.id == delegation_id,
        Delegation.committee_id == committee_id
    ).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="代表团不存在或不属于当前委员会")
    delegate.delegation_id = delegation_id
    db.commit()
    return {"message": "分配成功"}


# ==================== 代表团管理 ====================

@router.get("/delegations", response_model=List[DelegationOut])
def list_delegations(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    return db.query(Delegation).filter(Delegation.committee_id == committee_id).all()


@router.post("/delegations", response_model=DelegationOut)
def create_delegation(
    data: DelegationBase,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    delegation = Delegation(name=data.name, committee_id=committee_id)
    db.add(delegation)
    db.commit()
    db.refresh(delegation)
    return delegation


@router.delete("/delegations/{delegation_id}")
def delete_delegation(
    delegation_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    delegation = db.query(Delegation).filter(
        Delegation.id == delegation_id,
        Delegation.committee_id == committee_id
    ).first()
    if not delegation:
        raise HTTPException(status_code=404, detail="代表团不存在")
    # 检查是否有代表
    members = db.query(User).filter(User.delegation_id == delegation_id).count()
    if members > 0:
        raise HTTPException(status_code=400, detail=f"该代表团下有 {members} 名代表，请先移除代表")
    db.delete(delegation)
    db.commit()
    return {"message": "删除成功"}


# ==================== 议程管理 ====================

class AgendaItemCreate(BaseModel):
    title: str
    level: int = 1
    order: int = 0


class AgendaItemOut(BaseModel):
    id: int
    committee_id: int
    title: str
    level: int
    order: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("/agenda", response_model=List[AgendaItemOut])
def list_agenda(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    return db.query(AgendaItem).filter(
        AgendaItem.committee_id == committee_id
    ).order_by(AgendaItem.order).all()


@router.post("/agenda", response_model=AgendaItemOut)
def create_agenda_item(
    data: AgendaItemCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    item = AgendaItem(
        committee_id=committee_id,
        title=data.title,
        level=data.level,
        order=data.order
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class AgendaBatchImport(BaseModel):
    items: List[AgendaItemCreate]


@router.post("/agenda/batch")
def batch_import_agenda(
    data: AgendaBatchImport,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """批量导入议程"""
    committee_id = get_staff_committee(current_user)
    count = 0
    for item_data in data.items:
        item = AgendaItem(
            committee_id=committee_id,
            title=item_data.title,
            level=item_data.level,
            order=item_data.order
        )
        db.add(item)
        count += 1
    db.commit()
    return {"message": f"成功导入 {count} 项议程", "count": count}


@router.delete("/agenda/batch/all")
def delete_all_agenda(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """删除所有议程"""
    committee_id = get_staff_committee(current_user)
    count = db.query(AgendaItem).filter(
        AgendaItem.committee_id == committee_id
    ).delete()
    db.commit()
    return {"message": f"已删除 {count} 项议程", "count": count}


@router.delete("/agenda/{item_id}")
def delete_agenda_item(
    item_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    item = db.query(AgendaItem).filter(
        AgendaItem.id == item_id,
        AgendaItem.committee_id == committee_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="议程不存在")
    db.delete(item)
    db.commit()
    return {"message": "删除成功"}


@router.put("/agenda/{item_id}/activate")
def activate_agenda_item(
    item_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    # 取消当前活跃议程
    db.query(AgendaItem).filter(
        AgendaItem.committee_id == committee_id,
        AgendaItem.is_active == True
    ).update({"is_active": False})
    # 设置新活跃议程
    item = db.query(AgendaItem).filter(
        AgendaItem.id == item_id,
        AgendaItem.committee_id == committee_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="议程不存在")
    item.is_active = True
    db.commit()
    return {"message": "已激活"}


# ==================== 委员会信息 ====================

@router.get("/committee")
def get_committee_info(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="委员会不存在")
    return {
        "id": committee.id,
        "name": committee.name,
        "features": committee.features or []
    }


# ==================== 点名 ====================

@router.get("/rollcall")
def get_rollcall(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    """获取当前委员会的点名状态（按代表统计，显示席位）"""
    committee_id = get_staff_committee(current_user)
    delegations = db.query(Delegation).filter(Delegation.committee_id == committee_id).all()
    if not delegations:
        return []

    delegation_ids = [d.id for d in delegations]
    delegation_map = {d.id: d.name for d in delegations}
    
    delegates = db.query(User).filter(
        User.role == "delegate",
        User.delegation_id.in_(delegation_ids)
    ).order_by(User.delegation_id, User.is_leader.desc()).all()

    # 获取点名记录（按代表ID索引）
    rollcall_records = db.query(RollCall).filter(
        RollCall.committee_id == committee_id
    ).all()
    rollcall_map = {r.delegate_id: r.is_present for r in rollcall_records if r.delegate_id}

    result = []
    for m in delegates:
        result.append({
            "id": m.id,
            "delegation_id": m.delegation_id,
            "delegation_name": delegation_map.get(m.delegation_id, "未分配"),
            "seat": m.seat or delegation_map.get(m.delegation_id, "未分配"),
            "is_leader": m.is_leader,
            "is_present": rollcall_map.get(m.id, False)
        })
    return result


@router.put("/rollcall/{delegate_id}")
def update_delegate_rollcall(
    delegate_id: int,
    is_present: bool,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """更新某个代表的出席状态"""
    committee_id = get_staff_committee(current_user)
    delegate = db.query(User).filter(User.id == delegate_id, User.role == "delegate").first()
    if not delegate:
        raise HTTPException(status_code=404, detail="代表不存在")

    existing = db.query(RollCall).filter(
        RollCall.committee_id == committee_id,
        RollCall.delegate_id == delegate_id
    ).first()

    if existing:
        existing.is_present = is_present
    else:
        record = RollCall(
            committee_id=committee_id,
            delegation_id=delegate.delegation_id,
            delegate_id=delegate_id,
            is_present=is_present
        )
        db.add(record)

    db.commit()
    return {"message": "更新成功"}


# ==================== 会议主持 ====================

class MotionCreate(BaseModel):
    type: str  # moderated_caucus / unmoderated_caucus / speakers_list
    topic: str = ""
    unit_duration: int = 0
    total_duration: int = 0
    proposer_delegation_id: Optional[int] = None
    proposer_delegate_id: Optional[int] = None


class MotionOut(BaseModel):
    id: int
    committee_id: int
    type: str
    topic: str
    unit_duration: int
    total_duration: int
    status: str
    proposer_delegation_id: Optional[int] = None
    proposer_delegate_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True


@router.get("/motions")
def list_motions(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    motions = db.query(Motion).filter(Motion.committee_id == committee_id).order_by(Motion.created_at.desc()).all()
    
    result = []
    for m in motions:
        delegation = db.query(Delegation).filter(Delegation.id == m.proposer_delegation_id).first() if m.proposer_delegation_id else None
        delegate = db.query(User).filter(User.id == m.proposer_delegate_id).first() if m.proposer_delegate_id else None
        result.append({
            "id": m.id,
            "committee_id": m.committee_id,
            "type": m.type,
            "topic": m.topic,
            "unit_duration": m.unit_duration,
            "total_duration": m.total_duration,
            "status": m.status,
            "proposer_delegation_id": m.proposer_delegation_id,
            "proposer_delegation_name": delegation.name if delegation else None,
            "proposer_delegate_id": m.proposer_delegate_id,
            "proposer_delegate_name": delegate.username if delegate else None,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    return result


@router.post("/motions")
def create_motion(
    data: MotionCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    motion = Motion(
        committee_id=committee_id,
        type=data.type,
        topic=data.topic,
        unit_duration=data.unit_duration,
        total_duration=data.total_duration,
        proposer_delegation_id=data.proposer_delegation_id,
        proposer_delegate_id=data.proposer_delegate_id,
        status="active"
    )
    db.add(motion)
    db.commit()
    db.refresh(motion)
    return {
        "id": motion.id,
        "committee_id": motion.committee_id,
        "type": motion.type,
        "topic": motion.topic,
        "unit_duration": motion.unit_duration,
        "total_duration": motion.total_duration,
        "status": motion.status,
        "proposer_delegation_id": motion.proposer_delegation_id,
        "proposer_delegate_id": motion.proposer_delegate_id,
        "created_at": motion.created_at.isoformat() if motion.created_at else None
    }


@router.put("/motions/{motion_id}/status")
def update_motion_status(
    motion_id: int,
    status: str,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    motion = db.query(Motion).filter(
        Motion.id == motion_id,
        Motion.committee_id == committee_id
    ).first()
    if not motion:
        raise HTTPException(status_code=404, detail="动议不存在")
    motion.status = status
    db.commit()
    return {"message": "更新成功"}


@router.delete("/motions/{motion_id}")
def delete_motion(
    motion_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    motion = db.query(Motion).filter(
        Motion.id == motion_id,
        Motion.committee_id == committee_id
    ).first()
    if not motion:
        raise HTTPException(status_code=404, detail="动议不存在")
    db.delete(motion)
    db.commit()
    return {"message": "删除成功"}


# ==================== 发言名单 ====================

class SpeakerAdd(BaseModel):
    delegation_id: int
    delegate_id: Optional[int] = None


@router.get("/motions/{motion_id}/speakers")
def get_speakers(
    motion_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取发言名单"""
    speakers = db.query(SpeakerEntry).filter(
        SpeakerEntry.motion_id == motion_id
    ).order_by(SpeakerEntry.order).all()

    result = []
    for s in speakers:
        delegation = db.query(Delegation).filter(Delegation.id == s.delegation_id).first()
        delegate = db.query(User).filter(User.id == s.delegate_id).first() if s.delegate_id else None
        result.append({
            "id": s.id,
            "delegation_id": s.delegation_id,
            "delegation_name": delegation.name if delegation else "未知",
            "delegate_id": s.delegate_id,
            "delegate_name": delegate.username if delegate else None,
            "order": s.order,
            "has_spoken": s.has_spoken,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "duration": s.duration
        })
    return result


@router.post("/motions/{motion_id}/speakers")
def add_speaker(
    motion_id: int,
    data: SpeakerAdd,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """添加发言者到发言名单"""
    committee_id = get_staff_committee(current_user)
    motion = db.query(Motion).filter(
        Motion.id == motion_id,
        Motion.committee_id == committee_id
    ).first()
    if not motion:
        raise HTTPException(status_code=404, detail="动议不存在")

    # 获取当前最大排序
    max_order = db.query(SpeakerEntry).filter(
        SpeakerEntry.motion_id == motion_id
    ).count()

    speaker = SpeakerEntry(
        motion_id=motion_id,
        delegation_id=data.delegation_id,
        delegate_id=data.delegate_id,
        order=max_order + 1,
        has_spoken=0
    )
    db.add(speaker)
    db.commit()
    db.refresh(speaker)
    return {"message": "添加成功", "id": speaker.id}


@router.delete("/motions/{motion_id}/speakers/{speaker_id}")
def remove_speaker(
    motion_id: int,
    speaker_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """从发言名单中移除"""
    speaker = db.query(SpeakerEntry).filter(
        SpeakerEntry.id == speaker_id,
        SpeakerEntry.motion_id == motion_id
    ).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="发言者不存在")
    db.delete(speaker)
    db.commit()
    return {"message": "移除成功"}


@router.put("/motions/{motion_id}/speakers/{speaker_id}/start")
def start_speaking(
    motion_id: int,
    speaker_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """开始发言"""
    speaker = db.query(SpeakerEntry).filter(
        SpeakerEntry.id == speaker_id,
        SpeakerEntry.motion_id == motion_id
    ).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="发言者不存在")
    speaker.has_spoken = 0  # 标记为正在发言
    db.commit()
    return {"message": "已开始"}


@router.put("/motions/{motion_id}/speakers/{speaker_id}/end")
def end_speaking(
    motion_id: int,
    speaker_id: int,
    duration: int = 0,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """结束发言"""
    speaker = db.query(SpeakerEntry).filter(
        SpeakerEntry.id == speaker_id,
        SpeakerEntry.motion_id == motion_id
    ).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="发言者不存在")
    speaker.has_spoken = 1
    speaker.duration = duration
    db.commit()

    # 记录发言
    committee_id = get_staff_committee(current_user)
    record = SpeechRecord(
        delegation_id=speaker.delegation_id,
        committee_id=committee_id,
        motion_id=motion_id,
        duration=duration
    )
    db.add(record)
    db.commit()
    return {"message": "已结束"}


class SpeakerContentUpdate(BaseModel):
    content: str


@router.put("/motions/{motion_id}/speakers/{speaker_id}/content")
def update_speaker_content(
    motion_id: int,
    speaker_id: int,
    data: SpeakerContentUpdate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """更新发言内容"""
    speaker = db.query(SpeakerEntry).filter(
        SpeakerEntry.id == speaker_id,
        SpeakerEntry.motion_id == motion_id
    ).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="发言者不存在")
    speaker.content = data.content
    db.commit()
    return {"message": "更新成功"}


@router.get("/motions/{motion_id}/speakers/{speaker_id}")
def get_speaker_detail(
    motion_id: int,
    speaker_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取发言者详情（包括发言内容）"""
    speaker = db.query(SpeakerEntry).filter(
        SpeakerEntry.id == speaker_id,
        SpeakerEntry.motion_id == motion_id
    ).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="发言者不存在")
    delegation = db.query(Delegation).filter(Delegation.id == speaker.delegation_id).first()
    delegate = db.query(User).filter(User.id == speaker.delegate_id).first() if speaker.delegate_id else None
    return {
        "id": speaker.id,
        "motion_id": speaker.motion_id,
        "delegation_id": speaker.delegation_id,
        "delegation_name": delegation.name if delegation else "未知",
        "delegate_id": speaker.delegate_id,
        "delegate_name": delegate.username if delegate else None,
        "order": speaker.order,
        "has_spoken": speaker.has_spoken,
        "duration": speaker.duration,
        "content": speaker.content
    }


# ==================== 局势更新 ====================

class UpdateCreate(BaseModel):
    title: str
    content: str = ""
    type: str = "text"
    visibility: List[int] = []


@router.get("/updates")
def list_updates(
    keyword: str = None,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取局势更新列表，支持关键字搜索（包括附件内容）"""
    from utils.file_parser import extract_text_from_file
    
    committee_id = get_staff_committee(current_user)
    updates = db.query(Update).filter(Update.committee_id == committee_id).order_by(Update.created_at.desc()).all()
    
    if not keyword:
        return updates
    
    # 过滤匹配的结果
    result = []
    keyword_lower = keyword.lower()
    for u in updates:
        title_match = keyword_lower in (u.title or "").lower()
        content_match = keyword_lower in (u.content or "").lower()
        
        # 检查附件内容
        file_content_match = False
        if u.file_path and not (title_match or content_match):
            file_text = extract_text_from_file(u.file_path)
            file_content_match = keyword_lower in file_text.lower()
        
        if title_match or content_match or file_content_match:
            result.append(u)
    
    return result


@router.post("/updates")
def create_update(
    data: UpdateCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    update = Update(
        committee_id=committee_id,
        sender_id=current_user.id,
        title=data.title,
        content=data.content,
        type=data.type,
        visibility=data.visibility
    )
    db.add(update)
    db.commit()
    return {"message": "发布成功"}


@router.delete("/updates/{update_id}")
def delete_update(
    update_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    update = db.query(Update).filter(
        Update.id == update_id,
        Update.committee_id == committee_id
    ).first()
    if not update:
        raise HTTPException(status_code=404, detail="更新不存在")
    db.delete(update)
    db.commit()
    return {"message": "删除成功"}


# ==================== 指令/文件管理 ====================

@router.get("/directives")
def list_directives(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    directives = db.query(Directive).filter(Directive.committee_id == committee_id).order_by(Directive.created_at.desc()).all()
    
    result = []
    for d in directives:
        delegation = db.query(Delegation).filter(Delegation.id == d.delegation_id).first()
        result.append({
            "id": d.id,
            "committee_id": d.committee_id,
            "delegation_id": d.delegation_id,
            "delegation_name": delegation.name if delegation else "未知",
            "drafter": d.drafter,
            "admin_points": d.admin_points,
            "secrecy": d.secrecy,
            "content": d.content,
            "departments": d.departments or [],
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })
    return result


@router.put("/directives/{directive_id}/status")
def update_directive_status(
    directive_id: int,
    status: str,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    committee_id = get_staff_committee(current_user)
    directive = db.query(Directive).filter(
        Directive.id == directive_id,
        Directive.committee_id == committee_id
    ).first()
    if not directive:
        raise HTTPException(status_code=404, detail="指令不存在")
    directive.status = status
    db.commit()
    return {"message": "更新成功"}


@router.get("/documents")
def list_documents(
    keyword: str = None,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取文件列表，支持关键字搜索（包括 docx 附件内容）"""
    from utils.file_parser import extract_text_from_file
    
    committee_id = get_staff_committee(current_user)
    docs = db.query(Document).filter(Document.committee_id == committee_id).order_by(Document.created_at.desc()).all()
    
    result = []
    for d in docs:
        # 如果有关键字，先检查是否匹配
        if keyword:
            keyword_lower = keyword.lower()
            title_match = keyword_lower in (d.title or "").lower()
            content_match = keyword_lower in (d.content or "").lower()
            
            # 解析 docx 附件内容
            file_content_match = False
            if d.file_path and not (title_match or content_match):
                file_text = extract_text_from_file(d.file_path)
                file_content_match = keyword_lower in file_text.lower()
            
            if not (title_match or content_match or file_content_match):
                continue
        
        delegation = db.query(Delegation).filter(Delegation.id == d.delegation_id).first()
        # 解析签署国家名称
        signing_names = []
        if d.signing_countries:
            for cid in d.signing_countries:
                c = db.query(Delegation).filter(Delegation.id == cid).first()
                if c:
                    signing_names.append(c.name)
        result.append({
            "id": d.id,
            "type": "document",
            "committee_id": d.committee_id,
            "delegation_id": d.delegation_id,
            "delegation_name": delegation.name if delegation else "未知",
            "drafter": d.drafter,
            "doc_type": d.doc_type,
            "title": d.title,
            "content": d.content,
            "file_path": d.file_path,
            "signing_countries": d.signing_countries or [],
            "signing_country_names": signing_names,
            "secrecy": d.secrecy or "public",
            "published": d.published or False,
            "recalled": d.recalled or False,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })
    
    return result


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None


@router.put("/documents/{doc_id}")
def update_document(
    doc_id: int,
    data: DocumentUpdate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """编辑文件"""
    committee_id = get_staff_committee(current_user)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.committee_id == committee_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    if data.title is not None:
        doc.title = data.title
    if data.content is not None:
        doc.content = data.content
    if data.doc_type is not None:
        doc.doc_type = data.doc_type
    db.commit()
    return {"message": "更新成功"}


@router.put("/documents/{doc_id}/recall")
def recall_document(
    doc_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """撤回文件（不删除，仅让代表不可见）"""
    committee_id = get_staff_committee(current_user)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.committee_id == committee_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    doc.recalled = True
    db.commit()
    return {"message": "撤回成功"}


@router.put("/documents/{doc_id}/restore")
def restore_document(
    doc_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """恢复撤回的文件"""
    committee_id = get_staff_committee(current_user)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.committee_id == committee_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    doc.recalled = False
    db.commit()
    return {"message": "恢复成功"}


class DirectPublish(BaseModel):
    title: str
    doc_type: str = "declaration"
    content: str = ""


@router.post("/publish-direct")
def publish_direct(
    data: DirectPublish,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """主席团直接发布文件到会议文件"""
    committee_id = get_staff_committee(current_user)
    
    doc_type_labels = {"declaration": "声明", "memorandum": "备忘录", "agreement": "协定"}
    type_label = doc_type_labels.get(data.doc_type, data.doc_type)
    title = f"[{type_label}] {data.title}"
    content = f"主席团发布\n\n{data.content}"

    update = Update(
        committee_id=committee_id,
        sender_id=current_user.id,
        title=title,
        content=content,
        type="file",
        visibility=[]
    )
    db.add(update)
    db.commit()
    return {"message": "发布成功"}


class PublishToUpdates(BaseModel):
    visibility: List[int] = []


@router.post("/documents/{doc_id}/publish")
def publish_document_to_updates(
    doc_id: int,
    data: PublishToUpdates,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """将文件发布到会议文件"""
    committee_id = get_staff_committee(current_user)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.committee_id == committee_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 秘密协定不能发布
    if doc.doc_type == "agreement" and doc.secrecy == "secret":
        raise HTTPException(status_code=403, detail="秘密协定不能发布")

    # 获取代表团名称
    delegation = db.query(Delegation).filter(Delegation.id == doc.delegation_id).first()
    delegation_name = delegation.name if delegation else "未知"

    # 解析签署国家名称
    signing_names = []
    if doc.signing_countries:
        for cid in doc.signing_countries:
            c = db.query(Delegation).filter(Delegation.id == cid).first()
            if c:
                signing_names.append(c.name)

    doc_type_labels = {"declaration": "声明", "memorandum": "备忘录", "agreement": "协定"}
    type_label = doc_type_labels.get(doc.doc_type, doc.doc_type)
    title = f"[{type_label}] {doc.title}"

    # 内容包含起草人和签署国家信息
    content_parts = [f"来源代表团：{delegation_name}", f"起草人：{doc.drafter}"]
    if signing_names:
        content_parts.append(f"签署国家：{'、'.join(signing_names)}")
    content_parts.append(f"\n{doc.content or ''}")
    content = "\n".join(content_parts)

    update = Update(
        committee_id=committee_id,
        sender_id=current_user.id,
        title=title,
        content=content,
        type="file",
        file_path=doc.file_path,
        visibility=data.visibility
    )
    db.add(update)

    # 标记文档为已发布
    doc.published = True

    db.commit()
    return {"message": "发布成功"}


# ==================== 发言记录 ====================

@router.get("/records")
def list_records(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    committee_id = get_staff_committee(current_user)
    records = db.query(SpeechRecord).filter(
        SpeechRecord.committee_id == committee_id
    ).order_by(SpeechRecord.created_at.desc()).all()

    result = []
    for r in records:
        delegation = db.query(Delegation).filter(Delegation.id == r.delegation_id).first()
        # 查找对应的发言内容
        speaker = db.query(SpeakerEntry).filter(
            SpeakerEntry.motion_id == r.motion_id,
            SpeakerEntry.delegation_id == r.delegation_id
        ).first() if r.motion_id else None
        result.append({
            "id": r.id,
            "delegation_id": r.delegation_id,
            "delegation_name": delegation.name if delegation else "未知",
            "duration": r.duration,
            "content": speaker.content if speaker else None,
            "created_at": r.created_at.isoformat()
        })
    return result


@router.get("/records/stats")
def get_record_stats(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    """获取发言统计"""
    committee_id = get_staff_committee(current_user)
    records = db.query(SpeechRecord).filter(
        SpeechRecord.committee_id == committee_id
    ).all()

    stats = {}
    for r in records:
        if r.delegation_id not in stats:
            delegation = db.query(Delegation).filter(Delegation.id == r.delegation_id).first()
            stats[r.delegation_id] = {
                "delegation_id": r.delegation_id,
                "delegation_name": delegation.name if delegation else "未知",
                "count": 0,
                "total_duration": 0
            }
        stats[r.delegation_id]["count"] += 1
        stats[r.delegation_id]["total_duration"] += r.duration

    return sorted(stats.values(), key=lambda x: x["count"], reverse=True)


# ==================== 存档/恢复 ====================

import json
import os

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "archives")
os.makedirs(ARCHIVE_DIR, exist_ok=True)


@router.post("/archive")
def archive_meeting(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    """存档当前会议状态"""
    committee_id = get_staff_committee(current_user)

    data = {
        "committee_id": committee_id,
        "delegations": [],
        "agenda": [],
        "motions": [],
        "directives": [],
        "updates": [],
        "rollcall": []
    }

    # 代表团
    delegations = db.query(Delegation).filter(Delegation.committee_id == committee_id).all()
    for d in delegations:
        members = db.query(User).filter(User.delegation_id == d.id, User.role == "delegate").all()
        data["delegations"].append({
            "id": d.id, "name": d.name,
            "members": [{"id": m.id, "username": m.username, "is_leader": m.is_leader} for m in members]
        })

    # 议程
    agenda = db.query(AgendaItem).filter(AgendaItem.committee_id == committee_id).all()
    data["agenda"] = [{"id": a.id, "title": a.title, "level": a.level, "order": a.order, "is_active": a.is_active} for a in agenda]

    # 动议
    motions = db.query(Motion).filter(Motion.committee_id == committee_id).all()
    for m in motions:
        speakers = db.query(SpeakerEntry).filter(SpeakerEntry.motion_id == m.id).all()
        data["motions"].append({
            "id": m.id, "type": m.type, "topic": m.topic,
            "unit_duration": m.unit_duration, "total_duration": m.total_duration,
            "status": m.status,
            "speakers": [{"delegation_id": s.delegation_id, "has_spoken": s.has_spoken, "duration": s.duration} for s in speakers]
        })

    # 点名
    rollcall = db.query(RollCall).filter(RollCall.committee_id == committee_id).all()
    data["rollcall"] = [{"delegation_id": r.delegation_id, "is_present": r.is_present} for r in rollcall]

    # 保存文件
    from datetime import datetime
    filename = f"archive_{committee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"message": "存档成功", "filename": filename}


@router.get("/archives")
def list_archives(current_user: User = Depends(require_role("staff"))):
    """列出所有存档"""
    committee_id = get_staff_committee(current_user)
    files = []
    for f in os.listdir(ARCHIVE_DIR):
        if f.startswith(f"archive_{committee_id}_") and f.endswith(".json"):
            filepath = os.path.join(ARCHIVE_DIR, f)
            stat = os.stat(filepath)
            files.append({
                "filename": f,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    return sorted(files, key=lambda x: x["created_at"], reverse=True)


@router.post("/archives/{filename}/restore")
def restore_archive(
    filename: str,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """从存档恢复"""
    committee_id = get_staff_committee(current_user)
    filepath = os.path.join(ARCHIVE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="存档不存在")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("committee_id") != committee_id:
        raise HTTPException(status_code=403, detail="该存档不属于当前委员会")

    # 恢复点名状态
    db.query(RollCall).filter(RollCall.committee_id == committee_id).delete()
    for rc in data.get("rollcall", []):
        db.add(RollCall(committee_id=committee_id, delegation_id=rc["delegation_id"], is_present=rc["is_present"]))

    db.commit()
    return {"message": "恢复成功"}


# ==================== 主席团发布的文件 ====================

@router.get("/staff-files")
def list_staff_files(current_user: User = Depends(require_role("staff")), db: Session = Depends(get_db)):
    """获取主席团发布的文件（Updates with type=file）"""
    committee_id = get_staff_committee(current_user)
    
    staff_files = db.query(Update).filter(
        Update.committee_id == committee_id,
        Update.type == "file"
    ).order_by(Update.created_at.desc()).all()
    
    result = []
    for f in staff_files:
        sender = db.query(User).filter(User.id == f.sender_id).first()
        result.append({
            "id": f.id,
            "type": "staff_file",
            "drafter": sender.username if sender else "未知",
            "title": f.title,
            "content": f.content,
            "file_path": f.file_path,
            "created_at": f.created_at.isoformat() if f.created_at else None
        })
    return result


# ==================== 文件上传/下载 ====================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """主席团上传文件"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="只支持 .docx 文件")
    
    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {"filename": filename, "original_name": file.filename}


@router.post("/publish-with-file")
async def publish_with_file(
    title: str,
    doc_type: str = "declaration",
    content: str = "",
    file: UploadFile = File(None),
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """主席团发布带附件的文件"""
    committee_id = get_staff_committee(current_user)
    
    file_path = None
    if file and file.filename:
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="只支持 .docx 文件")
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        file_content = await file.read()
        with open(filepath, "wb") as f:
            f.write(file_content)
        file_path = filename
    
    doc_type_labels = {"declaration": "声明", "memorandum": "备忘录", "agreement": "协定"}
    type_label = doc_type_labels.get(doc_type, doc_type)
    update_title = f"[{type_label}] {title}"
    update_content = f"主席团发布\n\n{content}" if content else "主席团发布"
    
    update = Update(
        committee_id=committee_id,
        sender_id=current_user.id,
        title=update_title,
        content=update_content,
        type="file",
        file_path=file_path,
        visibility=[]
    )
    db.add(update)
    db.commit()
    return {"message": "发布成功"}


@router.get("/download/{filename}")
def download_file(
    filename: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """下载文件（支持 query parameter 传 token）"""
    if token:
        try:
            from jose import jwt
            from config import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="无效的认证凭据")
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role != "staff":
                raise HTTPException(status_code=403, detail="权限不足")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
    else:
        raise HTTPException(status_code=401, detail="缺少认证凭据")

    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)


# ==================== 时间线管理 ====================

from datetime import date as date_type, timedelta

class TimelineUpdate(BaseModel):
    conference_date: Optional[str] = None  # 格式: "2026-05-18"
    days_per_hour: Optional[float] = None  # 每现实小时 = x会议天


@router.get("/timeline")
def get_timeline(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取当前委员会的时间线设置"""
    committee_id = get_staff_committee(current_user)
    from models.timeline import Timeline
    
    timeline = db.query(Timeline).filter(Timeline.committee_id == committee_id).first()
    if not timeline:
        return {
            "conference_date": None,
            "days_per_hour": None,
            "current_date": None,
            "last_updated": None
        }
    
    # 计算当前会议日期
    now = datetime.utcnow()
    elapsed_hours = (now - timeline.last_updated).total_seconds() / 3600
    elapsed_days = elapsed_hours * timeline.hours_per_day
    current_date = timeline.conference_date + timedelta(days=elapsed_days)
    
    return {
        "conference_date": timeline.conference_date.isoformat(),
        "days_per_hour": timeline.hours_per_day,
        "current_date": current_date.isoformat(),
        "last_updated": timeline.last_updated.isoformat()
    }


@router.put("/timeline")
def update_timeline(
    data: TimelineUpdate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """更新时间线设置"""
    committee_id = get_staff_committee(current_user)
    from models.timeline import Timeline
    
    timeline = db.query(Timeline).filter(Timeline.committee_id == committee_id).first()
    
    # 解析日期
    new_date = None
    if data.conference_date:
        try:
            new_date = date_type.fromisoformat(data.conference_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    
    if not timeline:
        # 创建新的时间线
        now = datetime.utcnow()
        timeline = Timeline(
            committee_id=committee_id,
            conference_date=new_date or date_type.today(),
            hours_per_day=data.days_per_hour if data.days_per_hour is not None else 1.0,
            last_updated=now
        )
        db.add(timeline)
    else:
        # 更新现有时间线
        now = datetime.utcnow()
        
        if new_date is not None or data.days_per_hour is not None:
            # 先根据当前流速计算到现在的会议日期
            elapsed_hours = (now - timeline.last_updated).total_seconds() / 3600
            elapsed_days = elapsed_hours * timeline.hours_per_day
            current_date = timeline.conference_date + timedelta(days=elapsed_days)
            
            # 应用新的设置
            if new_date is not None:
                timeline.conference_date = new_date
            else:
                timeline.conference_date = current_date
            
            if data.days_per_hour is not None:
                timeline.hours_per_day = data.days_per_hour
            
            timeline.last_updated = now
    
    db.commit()
    db.refresh(timeline)
    
    # 返回更新后的当前日期
    elapsed_hours = (datetime.utcnow() - timeline.last_updated).total_seconds() / 3600
    elapsed_days = elapsed_hours * timeline.hours_per_day
    current_date = timeline.conference_date + timedelta(days=elapsed_days)
    
    return {
        "conference_date": timeline.conference_date.isoformat(),
        "days_per_hour": timeline.hours_per_day,
        "current_date": current_date.isoformat(),
        "last_updated": timeline.last_updated.isoformat()
    }
