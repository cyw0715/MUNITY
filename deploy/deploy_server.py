#!/usr/bin/env python3
"""
MUNITY OS 一键部署脚本
在服务器上执行：python3 deploy_server.py
"""
import os
import subprocess
import sys

PROJECT_DIR = "/home/deploy/mun-os"

def run(cmd, check=True):
    print(f"  执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  错误: {result.stderr}")
        return False
    return True

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  创建: {path}")

print("=" * 40)
print("  MUNITY OS 一键部署脚本")
print("=" * 40)

# 1. 安装依赖
print("\n[1/5] 安装系统依赖...")
run("apt update -qq")
run("apt install -y -qq python3 python3-pip python3-venv nginx curl")

# 安装 Node.js
print("\n[2/5] 安装 Node.js...")
if not os.path.exists("/usr/bin/node"):
    run("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
    run("apt install -y -qq nodejs")
else:
    print("  Node.js 已存在")

# 3. 创建后端
print("\n[3/5] 创建后端...")
backend_dir = os.path.join(PROJECT_DIR, "backend")

# requirements.txt
write_file(os.path.join(backend_dir, "requirements.txt"), """fastapi==0.115.0
uvicorn==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
""")

# config.py
write_file(os.path.join(backend_dir, "config.py"), '''import os

DATABASE_URL = "sqlite:///./mun_os.db"
SECRET_KEY = os.getenv("SECRET_KEY", "munity-os-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
''')

# database.py
write_file(os.path.join(backend_dir, "database.py"), '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''')

# models/__init__.py
write_file(os.path.join(backend_dir, "models/__init__.py"), '''from models.user import User
from models.committee import Committee
from models.delegation import Delegation
from models.motion import Motion, SpeakerEntry
from models.directive import Directive
from models.document import Document
from models.update import Update

__all__ = ["User", "Committee", "Delegation", "Motion", "SpeakerEntry", "Directive", "Document", "Update"]
''')

# models/user.py
write_file(os.path.join(backend_dir, "models/user.py"), '''from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=True)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    is_leader = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    committee = relationship("Committee", back_populates="staff_members", foreign_keys=[committee_id])
    delegation = relationship("Delegation", back_populates="members", foreign_keys=[delegation_id])
''')

# models/committee.py
write_file(os.path.join(backend_dir, "models/committee.py"), '''from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Committee(Base):
    __tablename__ = "committees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    features = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    staff_members = relationship("User", back_populates="committee", foreign_keys="User.committee_id")
    delegations = relationship("Delegation", back_populates="committee")
''')

# models/delegation.py
write_file(os.path.join(backend_dir, "models/delegation.py"), '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Delegation(Base):
    __tablename__ = "delegations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    committee = relationship("Committee", back_populates="delegations")
    members = relationship("User", back_populates="delegation", foreign_keys="User.delegation_id")
''')

# models/motion.py
write_file(os.path.join(backend_dir, "models/motion.py"), '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Motion(Base):
    __tablename__ = "motions"
    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    type = Column(String(30), nullable=False)
    topic = Column(String(200), nullable=True)
    unit_duration = Column(Integer, nullable=True)
    total_duration = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")
    proposer_delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=True)
    proposer_delegate_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    committee = relationship("Committee")
    speakers = relationship("SpeakerEntry", back_populates="motion")

class SpeakerEntry(Base):
    __tablename__ = "speakers_entries"
    id = Column(Integer, primary_key=True, index=True)
    motion_id = Column(Integer, ForeignKey("motions.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    delegate_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order = Column(Integer, default=0)
    has_spoken = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    motion = relationship("Motion", back_populates="speakers")
''')

# models/directive.py
write_file(os.path.join(backend_dir, "models/directive.py"), '''from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from database import Base

class Directive(Base):
    __tablename__ = "directives"
    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    drafter = Column(String(100), nullable=False)
    admin_points = Column(Integer, default=0)
    secrecy = Column(String(20), default="public")
    content = Column(Text, nullable=True)
    status = Column(String(20), default="unread")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
''')

# models/document.py
write_file(os.path.join(backend_dir, "models/document.py"), '''from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    delegation_id = Column(Integer, ForeignKey("delegations.id"), nullable=False)
    drafter = Column(String(100), nullable=False)
    doc_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    signing_countries = Column(JSON, nullable=True)
    secrecy = Column(String(20), default="public")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
''')

# models/update.py
write_file(os.path.join(backend_dir, "models/update.py"), '''from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from database import Base

class Update(Base):
    __tablename__ = "updates"
    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String(20), default="text")
    visibility = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
''')

# services/__init__.py
write_file(os.path.join(backend_dir, "services/__init__.py"), '''from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials=Depends(security), db=Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

def require_role(*roles):
    def checker(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker
''')

# main.py
write_file(os.path.join(backend_dir, "main.py"), '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import User
from services import hash_password
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

Base.metadata.create_all(bind=engine)
app = FastAPI(title="MUNITY OS", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first():
            db.add(User(username=DEFAULT_ADMIN_USERNAME, password_hash=hash_password(DEFAULT_ADMIN_PASSWORD), role="admin"))
            db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "MUNITY OS API", "version": "1.0.0"}

@app.post("/api/auth/login")
def login(username: str, password: str):
    from jose import jwt
    from config import SECRET_KEY, ALGORITHM
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = create_access_token({"user_id": user.id, "role": user.role})
        return {"access_token": token, "role": user.role, "user_id": user.id, "username": user.username}
    finally:
        db.close()

from services import verify_password, create_access_token
''')

# 安装 Python 依赖
print("  安装 Python 依赖...")
run(f"cd {backend_dir} && pip3 install -r requirements.txt --break-system-packages -q")

# 4. 创建前端（简化版）
print("\n[4/5] 创建前端...")
frontend_dir = os.path.join(PROJECT_DIR, "frontend")

# 创建一个简单的静态前端
write_file(os.path.join(frontend_dir, "dist/index.html"), '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MUNITY OS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.15); width: 380px; }
        h1 { text-align: center; font-size: 32px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #909399; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; border: 1px solid #dcdfe6; border-radius: 4px; margin-bottom: 16px; font-size: 14px; }
        input:focus { outline: none; border-color: #409eff; }
        button { width: 100%; padding: 12px; background: #409eff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background: #66b1ff; }
        .error { color: #f56c6c; text-align: center; margin-bottom: 16px; display: none; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>MUNITY OS</h1>
        <p class="subtitle">模拟联合国会议系统</p>
        <div class="error" id="error"></div>
        <input type="text" id="username" placeholder="用户名" value="admin">
        <input type="password" id="password" placeholder="密码" value="admin123">
        <button onclick="login()">登录</button>
    </div>
    <script>
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorEl = document.getElementById('error');
            errorEl.style.display = 'none';
            try {
                const res = await fetch('/api/auth/login?username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password), { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    localStorage.setItem('token', data.access_token);
                    localStorage.setItem('user', JSON.stringify(data));
                    alert('登录成功！角色：' + data.role);
                } else {
                    errorEl.textContent = data.detail || '登录失败';
                    errorEl.style.display = 'block';
                }
            } catch (e) {
                errorEl.textContent = '网络错误';
                errorEl.style.display = 'block';
            }
        }
        document.getElementById('password').addEventListener('keypress', e => { if (e.key === 'Enter') login(); });
    </script>
</body>
</html>
''')

# 5. 配置 Nginx 和服务
print("\n[5/5] 配置 Nginx 和服务...")

write_file("/etc/nginx/sites-available/munity", '''server {
    listen 80;
    server_name _;
    location / {
        root /home/deploy/mun-os/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
''')

run("ln -sf /etc/nginx/sites-available/munity /etc/nginx/sites-enabled/munity")
run("rm -f /etc/nginx/sites-enabled/default")
run("nginx -t && systemctl reload nginx")

write_file("/etc/systemd/system/munity.service", '''[Unit]
Description=MUNITY OS Backend
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/home/deploy/mun-os/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
''')

run("systemctl daemon-reload")
run("systemctl enable munity")
run("systemctl start munity")

# 设置权限
run(f"chown -R deploy:deploy {PROJECT_DIR}")

print("\n" + "=" * 40)
print("  部署完成！")
print("=" * 40)
print(f"\n访问地址：http://YOUR_SERVER_IP")
print("\n默认管理员：admin / admin123")
print("\n常用命令：")
print("  查看状态：sudo systemctl status munity")
print("  重启后端：sudo systemctl restart munity")
print("  查看日志：sudo journalctl -u munity -f")
