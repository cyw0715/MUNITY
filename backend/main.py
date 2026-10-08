from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from database import engine, Base, SessionLocal
from models import User, Committee
from services import hash_password, require_role, validate_password_strength
from routers import auth_router, admin_router, staff_router, delegate_router
from routers.vote import router as vote_router
from routers.async_message import router as async_message_router
from config import (
    CORS_ORIGINS,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ADMIN_PASSWORD,
)
from auto_save import auto_saver
from monitor import monitor, REALTIME_INTERVAL
import asyncio
import os
import secrets
import time
import logging

logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MUNITY OS", version="1.0.0")

# CORS 配置（白名单；不再使用 allow_origins=["*"] + credentials）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=bool(CORS_ORIGINS),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


MAX_JSON_BODY_BYTES = 1 * 1024 * 1024  # JSON 请求体上限（1MB）


@app.middleware("http")
async def limit_json_body(request: Request, call_next):
    """限制 JSON 请求体大小。

    文件上传走 multipart（另有 20MB 上限），这里只拦 application/json，
    否则一个超大 JSON 就能把内存吃满。
    """
    if request.method in ("POST", "PUT", "PATCH"):
        ctype = (request.headers.get("content-type") or "").lower()
        if ctype.startswith("application/json"):
            try:
                length = int(request.headers.get("content-length") or 0)
            except ValueError:
                length = 0
            if length > MAX_JSON_BODY_BYTES:
                # 先流式丢弃请求体再回 413：不读就直接响应，客户端会看到连接重置
                # 而不是这个错误码。用 stream() 逐块丢弃，避免把大 body 读进内存。
                try:
                    async for _ in request.stream():
                        pass
                except Exception:
                    pass
                return JSONResponse(
                    {"detail": f"请求体过大（上限 {MAX_JSON_BODY_BYTES // 1024 // 1024}MB）"},
                    status_code=413,
                )
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:",
    )
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


# 注册路由
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(staff_router)
app.include_router(delegate_router)
app.include_router(vote_router)
app.include_router(async_message_router)


# ==================== 实时监控推送 ====================

_realtime_task: asyncio.Task = None
_admin_ids_cache: dict = {"ids": [], "at": 0.0}
_ADMIN_CACHE_TTL = 60  # 管理员 ID 缓存时长（秒）


def _get_admin_ids() -> list:
    """获取管理员 ID 列表（带缓存，避免每 2 秒查库）"""
    now = time.time()
    if now - _admin_ids_cache["at"] < _ADMIN_CACHE_TTL:
        return _admin_ids_cache["ids"]
    db = SessionLocal()
    try:
        ids = [u.id for u in db.query(User).filter(User.role == "admin").all()]
    except Exception as e:
        logger.warning("查询管理员列表失败: %s", e)
        ids = _admin_ids_cache["ids"]
    finally:
        db.close()
    _admin_ids_cache["ids"] = ids
    _admin_ids_cache["at"] = now
    return ids


async def _realtime_monitor_task():
    """每 REALTIME_INTERVAL 秒采样一次，并通过 WebSocket 推送给在线管理员"""
    from services.websocket_manager import ws_manager

    logger.info("实时监控推送已启动（间隔 %ss）", REALTIME_INTERVAL)
    # 先等一个采样周期：预热基线刚建立，立刻采样会得到无意义的 0%
    await asyncio.sleep(REALTIME_INTERVAL)
    while True:
        try:
            snapshot = monitor.sample_realtime()
            if snapshot:
                admin_ids = _get_admin_ids()
                if admin_ids:
                    payload = {
                        "type": "system_metrics",
                        "interval": REALTIME_INTERVAL,
                        "data": snapshot,
                    }
                    for uid in admin_ids:
                        await ws_manager.send_to_user(uid, payload)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("实时监控推送失败: %s", e)
        await asyncio.sleep(REALTIME_INTERVAL)


@app.on_event("startup")
def on_startup():
    """启动时初始化"""
    monitor.start()
    auto_saver.restore_state()

    # 初始化默认管理员：优先环境变量；未提供则仅开发环境创建随机口令
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not existing:
            password = DEFAULT_ADMIN_PASSWORD
            generated = False
            if not password:
                password = secrets.token_urlsafe(12)
                generated = True
            validate_password_strength(password)
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(password),
                role="admin"
            )
            db.add(admin)
            db.commit()
            if generated:
                logger.warning(
                    "默认管理员 %s 已创建，一次性随机密码: %s （请立即登录并修改）",
                    DEFAULT_ADMIN_USERNAME,
                    password,
                )
            else:
                logger.info("默认管理员 %s 已创建", DEFAULT_ADMIN_USERNAME)
    finally:
        db.close()

    auto_saver.start()


@app.on_event("startup")
async def start_realtime_monitor():
    """启动实时监控推送任务。

    必须声明为 async：同步的 startup 处理器会被 Starlette 放到线程池执行，
    那里没有运行中的事件循环，asyncio.create_task 会直接抛错。
    """
    global _realtime_task
    _realtime_task = asyncio.create_task(_realtime_monitor_task())


@app.on_event("shutdown")
async def stop_realtime_monitor():
    """取消实时监控推送任务（需在事件循环内取消，保证线程安全）"""
    global _realtime_task
    if _realtime_task and not _realtime_task.done():
        _realtime_task.cancel()
        try:
            await _realtime_task
        except asyncio.CancelledError:
            pass
    _realtime_task = None


@app.on_event("shutdown")
def on_shutdown():
    """关闭时保存状态"""
    monitor.stop()
    auto_saver.stop()
    auto_saver._save_state()
    print("[AutoSave] 关闭前状态已保存")


@app.get("/api/system/status")
def system_status(current_user=Depends(require_role("admin"))):
    """系统状态接口（仅管理员）"""
    save_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_saves", "meeting_state.json")
    last_save = None
    if os.path.exists(save_file):
        import json
        with open(save_file, "r") as f:
            data = json.load(f)
            last_save = data.get("saved_at")
    return {
        "auto_save_enabled": True,
        "save_interval": 30,
        "last_save": last_save
    }


@app.get("/api/system/monitor")
def server_monitor(scope: str = "current", current_user=Depends(require_role("admin"))):
    """服务器资源监控接口（仅管理员）

    scope=current 返回当前指标
    scope=1m 返回最近1分钟 + 当前
    scope=24h 返回最近24小时历史 + 当前
    """
    current = monitor.get_current()

    if scope == "current":
        return {"current": current}

    history = monitor.get_history(minutes=1 if scope == "1m" else 1440)

    cpu_data = []
    mem_data = []
    for h in history:
        t = int(h["timestamp"]) * 1000
        cpu_data.append([t, h["cpu_percent"]])
        mem_data.append([t, h["mem_percent"]])

    return {
        "current": current,
        "cpu": cpu_data,
        "mem": mem_data,
    }


@app.get("/api/system/monitor/realtime")
def server_monitor_realtime(current_user=Depends(require_role("admin"))):
    """实时监控初始数据（仅管理员）

    返回最近 2 分钟的实时采样序列，供前端首屏填充滚动图表；
    后续增量数据由 WebSocket 的 system_metrics 事件推送。
    """
    return {
        "current": monitor.get_current(),
        "series": monitor.get_realtime_history(seconds=120),
        "interval": REALTIME_INTERVAL,
    }


@app.get("/api/committee-logo/{committee_id}")
def committee_logo(committee_id: int):
    """委员会侧边栏图标（公开只读）。

    文件名来自数据库而非 URL，且仅允许白名单图片格式，无路径穿越风险。
    """
    from models.committee import Committee
    from utils.committee_logo import logo_path

    db = SessionLocal()
    try:
        committee = db.query(Committee).filter(Committee.id == committee_id).first()
        stored = committee.logo_image if committee else None
    finally:
        db.close()

    path = logo_path(stored)
    if not path:
        return JSONResponse({"detail": "未设置图标"}, status_code=404)
    return FileResponse(path)


# 静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

# 挂载静态文件
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "MUNITY OS API", "version": "1.0.0", "note": "Frontend not built. Run 'npm run build' in frontend directory."}
