from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器，维护用户连接和消息推送"""

    def __init__(self):
        # { user_id: [WebSocket, ...] }
        self.active_connections: Dict[int, list[WebSocket]] = {}
        # { user_id: set of committee_ids }
        self.user_committees: Dict[int, set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, committee_id: int = None):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        if committee_id is not None:
            if user_id not in self.user_committees:
                self.user_committees[user_id] = set()
            self.user_committees[user_id].add(committee_id)
        logger.info(f"WebSocket 用户 {user_id} 已连接 (共 {self._total_connections()} 个连接)")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                conn for conn in self.active_connections[user_id]
                if conn != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_committees:
                    del self.user_committees[user_id]
        logger.info(f"WebSocket 用户 {user_id} 已断开 (剩余 {self._total_connections()} 个连接)")

    def _total_connections(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    async def send_to_user(self, user_id: int, message: dict):
        """向指定用户的所有连接发送消息"""
        if user_id not in self.active_connections:
            return
        dead_connections = []
        for conn in self.active_connections[user_id]:
            try:
                await conn.send_json(message)
            except Exception:
                dead_connections.append(conn)
        for conn in dead_connections:
            self.disconnect(conn, user_id)

    async def send_to_delegation(self, delegation_id: int, message: dict, db_session=None):
        """向指定代表团的所有成员发送消息"""
        if db_session:
            from models.user import User
            members = db_session.query(User).filter(
                User.delegation_id == delegation_id,
                User.role == "delegate"
            ).all()
            for member in members:
                await self.send_to_user(member.id, message)

    async def send_to_committee_staff(self, committee_id: int, message: dict, db_session=None):
        """向指定委员会的所有学团成员发送消息"""
        if db_session:
            from models.user import User
            staff = db_session.query(User).filter(
                User.committee_id == committee_id,
                User.role.in_(["staff", "admin"])
            ).all()
            for s in staff:
                await self.send_to_user(s.id, message)

    async def broadcast_committee(self, committee_id: int, message: dict):
        """向指定委员会的所有在线用户广播"""
        for uid, committees in self.user_committees.items():
            if committee_id in committees:
                await self.send_to_user(uid, message)

    async def send_to_committee_members(self, committee_id: int, message: dict, db_session=None):
        """向指定委员会的所有用户广播（通过数据库查询，不依赖 WS 注册的 committee）"""
        if db_session:
            from models.user import User
            members = db_session.query(User).filter(
                User.committee_id == committee_id
            ).all()
            for m in members:
                await self.send_to_user(m.id, message)

    async def broadcast(self, message: dict):
        """向所有在线用户广播"""
        for uid in list(self.active_connections.keys()):
            await self.send_to_user(uid, message)


# 全局单例
ws_manager = WebSocketManager()
