from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from database import get_db
from models.user import User
from models.delegation import Delegation
from models.async_message import AsyncMessage
from services import require_role, get_current_user
from services.websocket_manager import ws_manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["非对称消息"])


# ==================== Schema ====================

class AsyncMessageCreate(BaseModel):
    receiver_id: Optional[int] = None
    receiver_delegation_id: Optional[int] = None
    title: str
    content: str = ""
    visibility: str = "private"  # public / delegation / private


class AsyncMessageOut(BaseModel):
    id: int
    committee_id: int
    sender_id: int
    sender_name: str = ""
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


class AsyncMessageUpdate(BaseModel):
    is_read: bool = True


# ==================== 辅助函数 ====================

def get_staff_committee(current_user: User) -> int:
    """获取学团所属委员会ID"""
    if not current_user.committee_id:
        raise HTTPException(status_code=400, detail="您尚未分配到任何委员会")
    return current_user.committee_id


def msg_to_dict(msg: AsyncMessage, db: Session) -> dict:
    """将消息对象转为带关联字段的字典"""
    sender = db.query(User).filter(User.id == msg.sender_id).first()
    receiver = db.query(User).filter(User.id == msg.receiver_id).first() if msg.receiver_id else None
    delegation = db.query(Delegation).filter(Delegation.id == msg.receiver_delegation_id).first() if msg.receiver_delegation_id else None
    return {
        "id": msg.id,
        "committee_id": msg.committee_id,
        "sender_id": msg.sender_id,
        "sender_name": sender.seat or sender.username if sender else "未知",
        "receiver_id": msg.receiver_id,
        "receiver_name": receiver.seat or receiver.username if receiver else None,
        "receiver_delegation_id": msg.receiver_delegation_id,
        "receiver_delegation_name": delegation.name if delegation else None,
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
    """WebSocket 连接端点（简化版，生产环境应加强鉴权）"""
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            # 保持连接活跃，接收心跳
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
    """学团查看本委员会所有非对称消息"""
    committee_id = get_staff_committee(current_user)
    query = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id == committee_id
    )
    if visibility:
        query = query.filter(AsyncMessage.visibility == visibility)
    messages = query.order_by(AsyncMessage.created_at.desc()).all()
    return [msg_to_dict(m, db) for m in messages]


@router.post("/staff/async-messages", response_model=AsyncMessageOut)
def staff_create_async_message(
    data: AsyncMessageCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """学团发布非对称消息"""
    committee_id = get_staff_committee(current_user)

    # 验证接收者（如果指定了）
    if data.receiver_id:
        receiver = db.query(User).filter(
            User.id == data.receiver_id,
            User.role == "delegate"
        ).first()
        if not receiver:
            raise HTTPException(status_code=404, detail="接收代表不存在")
    if data.receiver_delegation_id:
        delegation = db.query(Delegation).filter(
            Delegation.id == data.receiver_delegation_id,
            Delegation.committee_id == committee_id
        ).first()
        if not delegation:
            raise HTTPException(status_code=404, detail="代表团不存在或不属于当前委员会")

    msg = AsyncMessage(
        committee_id=committee_id,
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        receiver_delegation_id=data.receiver_delegation_id,
        title=data.title,
        content=data.content,
        visibility=data.visibility,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # WebSocket 推送通知（异步，出错不影响消息保存）
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ws_payload = {
            "type": "new_async_message",
            "message": msg_to_dict(msg, db)
        }
        if data.receiver_id:
            loop.run_until_complete(ws_manager.send_to_user(data.receiver_id, ws_payload))
        elif data.receiver_delegation_id:
            loop.run_until_complete(ws_manager.send_to_delegation(data.receiver_delegation_id, ws_payload, db))
        else:
            loop.run_until_complete(ws_manager.broadcast_committee(committee_id, ws_payload))
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
    committee_id = get_staff_committee(current_user)
    msg = db.query(AsyncMessage).filter(
        AsyncMessage.id == message_id,
        AsyncMessage.committee_id == committee_id
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
    messages = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id == current_user.committee_id
    ).filter(
        # 条件：公开消息 OR 发给代表本人 OR 发给代表所属代表团
        (AsyncMessage.visibility == "public") |
        (AsyncMessage.receiver_id == user.id) |
        ((AsyncMessage.visibility == "delegation") & 
         (AsyncMessage.receiver_delegation_id == user.delegation_id))
    ).order_by(AsyncMessage.created_at.desc()).all()
    return [msg_to_dict(m, db) for m in messages]


@router.put("/delegate/async-messages/{message_id}/read")
def delegate_mark_read(
    message_id: int,
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表标记消息为已读"""
    msg = db.query(AsyncMessage).filter(
        AsyncMessage.id == message_id,
        AsyncMessage.receiver_id == current_user.id
    ).first()
    if not msg:
        # 也允许标记发给代表团的公开消息
        msg = db.query(AsyncMessage).filter(
            AsyncMessage.id == message_id,
            AsyncMessage.committee_id == current_user.committee_id
        ).first()
        if not msg:
            raise HTTPException(status_code=404, detail="消息不存在")
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
    count = db.query(AsyncMessage).filter(
        AsyncMessage.committee_id == current_user.committee_id,
        AsyncMessage.is_read == False
    ).filter(
        (AsyncMessage.visibility == "public") |
        (AsyncMessage.receiver_id == user.id) |
        ((AsyncMessage.visibility == "delegation") & 
         (AsyncMessage.receiver_delegation_id == user.delegation_id))
    ).count()
    return {"count": count}
