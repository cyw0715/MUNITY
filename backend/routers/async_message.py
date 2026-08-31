from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from database import get_db
from models.user import User
from models.delegation import Delegation
from models.committee import Committee
from models.async_message import AsyncMessage, get_receiver_ids, get_receiver_delegation_ids, is_message_visible_to
from services import require_role, get_current_user
from services.websocket_manager import ws_manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["非对称消息"])


# ==================== Schema ====================

class AsyncMessageCreate(BaseModel):
    receiver_ids: List[int] = []            # 多代表
    receiver_delegation_ids: List[int] = []  # 多代表团
    receiver_id: Optional[int] = None        # 兼容旧版
    receiver_delegation_id: Optional[int] = None  # 兼容旧版
    title: str
    content: str = ""
    visibility: str = "private"  # public / delegation / private


class AsyncMessageOut(BaseModel):
    id: int
    committee_id: int
    sender_id: int
    sender_name: str = ""
    receiver_ids: List[int] = []
    receiver_names: List[str] = []
    receiver_delegation_ids: List[int] = []
    receiver_delegation_names: List[str] = []
    receiver_id: Optional[int] = None
    receiver_name: Optional[str] = None
    receiver_delegation_id: Optional[int] = None
    receiver_delegation_name: Optional[str] = None
    title: str
    content: str
    visibility: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 辅助函数 ====================

def get_staff_committee_list(current_user: User) -> list[int]:
    """获取学团的所有可访问委员会ID"""
    from sqlalchemy import text
    from database import engine
    
    committee_ids = set()
    # 从 staff_committees 表获取
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT committee_id FROM staff_committees WHERE staff_id = :sid"),
            {"sid": current_user.id}
        )
        for row in result:
            committee_ids.add(row[0])
    
    # 兼容旧版 committee_id 字段
    if current_user.committee_id:
        committee_ids.add(current_user.committee_id)
    
    if not committee_ids:
        raise HTTPException(status_code=400, detail="您尚未分配到任何委员会")
    return sorted(committee_ids)


def get_primary_committee(current_user: User) -> int:
    """获取学团的主委员会（默认用第一个）"""
    committees = get_staff_committee_list(current_user)
    # 优先用 primary committee_id
    if current_user.committee_id and current_user.committee_id in committees:
        return current_user.committee_id
    return committees[0]


def msg_to_dict(msg: AsyncMessage, db: Session) -> dict:
    """将消息对象转为带关联字段的字典"""
    sender = db.query(User).filter(User.id == msg.sender_id).first()
    
    recv_ids = get_receiver_ids(msg)
    recv_dlg_ids = get_receiver_delegation_ids(msg)
    
    receiver_names = []
    for rid in recv_ids:
        u = db.query(User).filter(User.id == rid).first()
        receiver_names.append(u.seat or u.username if u else f"用户{rid}")
    
    delegation_names = []
    for did in recv_dlg_ids:
        d = db.query(Delegation).filter(Delegation.id == did).first()
        delegation_names.append(d.name if d else f"代表团{did}")
    
    # 兼容旧字段
    old_receiver = db.query(User).filter(User.id == msg.receiver_id).first() if msg.receiver_id else None
    old_delegation = db.query(Delegation).filter(Delegation.id == msg.receiver_delegation_id).first() if msg.receiver_delegation_id else None
    
    return {
        "id": msg.id,
        "committee_id": msg.committee_id,
        "sender_id": msg.sender_id,
        "sender_name": sender.seat or sender.username if sender else "未知",
        "receiver_ids": recv_ids,
        "receiver_names": receiver_names,
        "receiver_delegation_ids": recv_dlg_ids,
        "receiver_delegation_names": delegation_names,
        "receiver_id": msg.receiver_id if not recv_ids else (recv_ids[0] if len(recv_ids) == 1 else None),
        "receiver_name": old_receiver.seat or old_receiver.username if old_receiver else (receiver_names[0] if len(receiver_names) == 1 else None),
        "receiver_delegation_id": msg.receiver_delegation_id if not recv_dlg_ids else (recv_dlg_ids[0] if len(recv_dlg_ids) == 1 else None),
        "receiver_delegation_name": old_delegation.name if old_delegation else (delegation_names[0] if len(delegation_names) == 1 else None),
        "title": msg.title,
        "content": msg.content or "",
        "visibility": msg.visibility,
        "is_read": msg.is_read,
        "read_at": msg.read_at.isoformat() if msg.read_at else None,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


# ==================== WebSocket 端点 ====================

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket 连接端点"""
    committee_id = None
    from database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            committee_id = user.committee_id
    except Exception:
        pass
    finally:
        db.close()

    await ws_manager.connect(websocket, user_id, committee_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception:
        ws_manager.disconnect(websocket, user_id)


# ==================== 学团端 API ====================

@router.get("/staff/async-messages", response_model=List[AsyncMessageOut])
def staff_list_async_messages(
    visibility: Optional[str] = None,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """学团查看所有可访问委员会的非对称消息"""
    committee_ids = get_staff_committee_list(current_user)
    query = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id.in_(committee_ids)
    )
    if visibility:
        query = query.filter(AsyncMessage.visibility == visibility)
    messages = query.order_by(AsyncMessage.created_at.desc()).all()
    return [msg_to_dict(m, db) for m in messages]


@router.get("/staff/my-committees")
def staff_my_committees(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """学团获取自己的委员会列表"""
    from sqlalchemy import text
    from database import engine
    
    committees = []
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT c.id, c.name FROM committees c "
                 "JOIN staff_committees sc ON c.id = sc.committee_id "
                 "WHERE sc.staff_id = :sid"),
            {"sid": current_user.id}
        )
        committees = [{"id": row[0], "name": row[1]} for row in result]
    
    # 兼容旧版
    if not committees and current_user.committee_id:
        c = db.query(Committee).filter(Committee.id == current_user.committee_id).first()
        if c:
            committees = [{"id": c.id, "name": c.name}]
    
    return committees


@router.get("/staff/available-delegates")
def staff_available_delegates(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取学团可选的代表和代表团（跨委员会）"""
    committee_ids = get_staff_committee_list(current_user)
    delegations = db.query(Delegation).filter(
        Delegation.committee_id.in_(committee_ids)
    ).all()
    delegation_ids = [d.id for d in delegations]
    
    delegates = db.query(User).filter(
        User.role == "delegate",
        User.delegation_id.in_(delegation_ids)
    ).all()
    
    return {
        "delegations": [
            {"id": d.id, "name": d.name, "committee_id": d.committee_id}
            for d in delegations
        ],
        "delegates": [
            {"id": u.id, "username": u.username, "seat": u.seat,
             "delegation_id": u.delegation_id, "is_leader": u.is_leader}
            for u in delegates
        ]
    }


@router.post("/staff/async-messages", response_model=AsyncMessageOut)
def staff_create_async_message(
    data: AsyncMessageCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """学团发布非对称消息（支持多接收者）"""
    committee_ids = get_staff_committee_list(current_user)
    committee_id = get_primary_committee(current_user)

    # 合并旧版字段
    recv_ids = list(set(data.receiver_ids or []))
    recv_dlg_ids = list(set(data.receiver_delegation_ids or []))
    if data.receiver_id and data.receiver_id not in recv_ids:
        recv_ids.append(data.receiver_id)
    if data.receiver_delegation_id and data.receiver_delegation_id not in recv_dlg_ids:
        recv_dlg_ids.append(data.receiver_delegation_id)

    # 验证接收者
    if recv_ids:
        receivers = db.query(User).filter(
            User.id.in_(recv_ids),
            User.role == "delegate"
        ).all()
        found_ids = {u.id for u in receivers}
        for rid in recv_ids:
            if rid not in found_ids:
                raise HTTPException(status_code=404, detail=f"接收代表不存在 (id={rid})")

    if recv_dlg_ids:
        delegations = db.query(Delegation).filter(
            Delegation.id.in_(recv_dlg_ids),
            Delegation.committee_id.in_(committee_ids)
        ).all()
        found_ids = {d.id for d in delegations}
        for did in recv_dlg_ids:
            if did not in found_ids:
                raise HTTPException(status_code=404, detail=f"代表团不存在 (id={did})")

    msg = AsyncMessage(
        committee_id=committee_id,
        sender_id=current_user.id,
        receiver_id=recv_ids[0] if len(recv_ids) == 1 else (recv_ids[0] if recv_ids else None),
        receiver_delegation_id=recv_dlg_ids[0] if len(recv_dlg_ids) == 1 else (recv_dlg_ids[0] if recv_dlg_ids else None),
        receiver_ids=json.dumps(recv_ids),
        receiver_delegation_ids=json.dumps(recv_dlg_ids),
        title=data.title,
        content=data.content,
        visibility=data.visibility,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # WebSocket 推送
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ws_payload = {
            "type": "new_async_message",
            "message": msg_to_dict(msg, db)
        }
        if recv_ids:
            for uid in recv_ids:
                loop.run_until_complete(ws_manager.send_to_user(uid, ws_payload))
        if recv_dlg_ids:
            for did in recv_dlg_ids:
                loop.run_until_complete(ws_manager.send_to_delegation(did, ws_payload, db))
        if data.visibility == "public" or (not recv_ids and not recv_dlg_ids):
            for cid in committee_ids:
                loop.run_until_complete(ws_manager.broadcast_committee(cid, ws_payload))
        loop.close()
    except Exception as e:
        logger.warning(f"WebSocket 推送失败（消息已保存）: {e}")

    return msg_to_dict(msg, db)


@router.delete("/staff/async-messages/{message_id}")
def staff_delete_async_message(
    message_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """学团撤回非对称消息"""
    committee_ids = get_staff_committee_list(current_user)
    msg = db.query(AsyncMessage).filter(
        AsyncMessage.id == message_id,
        AsyncMessage.committee_id.in_(committee_ids)
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    db.delete(msg)
    db.commit()
    return {"message": "撤回成功"}


# ==================== 代表端 API ====================

@router.get("/delegate/async-messages", response_model=List[AsyncMessageOut])
def delegate_list_async_messages(
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表查看自己可见的非对称消息"""
    user = current_user
    # 获取同委员会的所有可见消息
    messages = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id == current_user.committee_id
    ).order_by(AsyncMessage.created_at.desc()).all()
    
    # 过滤可见性
    result = []
    for m in messages:
        if m.visibility == "public":
            result.append(m)
        elif user.id in get_receiver_ids(m):
            result.append(m)
        elif m.visibility == "delegation" and user.delegation_id in get_receiver_delegation_ids(m):
            result.append(m)
    return [msg_to_dict(m, db) for m in result]


@router.put("/delegate/async-messages/{message_id}/read")
def delegate_mark_read(
    message_id: int,
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表标记消息为已读"""
    msg = db.query(AsyncMessage).filter(
        AsyncMessage.id == message_id,
        AsyncMessage.committee_id == current_user.committee_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 更新 read_by 数组
    try:
        read_by = json.loads(msg.read_by) if msg.read_by and msg.read_by != "[]" else []
    except Exception:
        read_by = []
    
    # 添加当前用户的已读记录
    existing = [r for r in read_by if r.get("user_id") == current_user.id]
    if not existing:
        read_by.append({
            "user_id": current_user.id,
            "is_read": True,
            "read_at": datetime.now(timezone.utc).isoformat()
        })
    
    msg.read_by = json.dumps(read_by)
    
    # 旧字段兼容
    msg.is_read = True
    msg.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "已标记为已读"}


@router.get("/delegate/async-messages/unread-count")
def delegate_unread_count(
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表获取未读消息数量"""
    user = current_user
    messages = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id == current_user.committee_id
    ).all()
    
    unread = 0
    for m in messages:
        if not is_message_visible_to(m, user.id, user.delegation_id):
            continue
        try:
            read_by = json.loads(m.read_by) if m.read_by and m.read_by != "[]" else []
        except Exception:
            read_by = []
        if not any(r.get("user_id") == user.id for r in read_by):
            unread += 1
    return {"count": unread}
