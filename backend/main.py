from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from models import User, Committee
from services import hash_password
from routers import auth_router, admin_router, staff_router, delegate_router
from routers.vote import router as vote_router
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from auto_save import auto_saver
import os

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MUNITY OS", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(staff_router)
app.include_router(delegate_router)
app.include_router(vote_router)


@app.on_event("startup")
def on_startup():
    """启动时初始化"""
    # 尝试恢复上次状态
    auto_saver.restore_state()

    # 初始化默认管理员
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        if not existing:
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role="admin"
            )
            db.add(admin)
            db.commit()
            print(f"默认管理员已创建: {DEFAULT_ADMIN_USERNAME}")
    finally:
        db.close()

    # 启动自动保存
    auto_saver.start()


@app.on_event("shutdown")
def on_shutdown():
    """关闭时保存状态"""
    auto_saver.stop()
    auto_saver._save_state()
    print("[AutoSave] 关闭前状态已保存")


@app.get("/api/system/status")
def system_status():
    """系统状态接口"""
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


# 静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

# 挂载静态文件
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    
    # SPA路由 - 所有非API路由都返回index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # 如果是API路由，返回404
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        # 否则返回index.html
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "MUNITY OS API", "version": "1.0.0", "note": "Frontend not built. Run 'npm run build' in frontend directory."}