from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> None:
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"密码至少 {MIN_PASSWORD_LENGTH} 位")
    if password.lower() in {
        "admin123", "123456", "12345678", "password", "qwerty",
        "abc123", "111111", "123123", "iloveyou", "admin888",
        "123", "1234", "12345", "000000", "654321",
    }:
        raise HTTPException(status_code=400, detail="密码过于常见，请更换")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_user_from_token(token: str, db: Session) -> User:
    """供 WebSocket / 下载 query 等旁路复用，统一 JWT 解析。"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少认证凭据")
    payload = decode_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证凭据")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return role_checker


FEATURE_LABELS = {
    "agenda": "议程管理",
    "directives": "指令管理",
    "updates": "局势更新",
    "timeline": "时间线",
    "main_speakers": "主发言名单",
    "directive_points": "指令·行政点数",
}


def _resolve_committee_id(db: Session, user: User):
    """解析用户当前所属会场。

    学团优先取当前选中的会场（需在 staff_committees 中有效），
    代表经所属代表团解析——与 routers 内的同名逻辑保持一致。
    """
    from sqlalchemy import text

    if user.role == "staff":
        if user.committee_id:
            row = db.execute(
                text("SELECT 1 FROM staff_committees WHERE staff_id = :sid AND committee_id = :cid"),
                {"sid": user.id, "cid": user.committee_id}).first()
            if row:
                return user.committee_id
        row = db.execute(
            text("SELECT committee_id FROM staff_committees WHERE staff_id = :sid"),
            {"sid": user.id}).first()
        return row[0] if row else user.committee_id

    if user.role == "delegate":
        from models.delegation import Delegation
        if not user.delegation_id:
            return None
        delegation = db.query(Delegation).filter(Delegation.id == user.delegation_id).first()
        return delegation.committee_id if delegation else None

    return user.committee_id


def require_feature(feature: str, *roles: str):
    """依赖：要求当前用户所属会场启用了指定功能，否则 403。

    同时可兼做角色校验（传入 roles）。管理员不受会场功能限制
    （需要跨会场管理），但仍会校验角色。
    """
    def feature_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if roles and current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        if current_user.role == "admin":
            return current_user

        committee_id = _resolve_committee_id(db, current_user)
        if committee_id is None:
            raise HTTPException(status_code=403, detail="您尚未分配到任何会场")

        from models.committee import Committee
        committee = db.query(Committee).filter(Committee.id == committee_id).first()
        features = (committee.features or []) if committee else []
        if feature not in features:
            label = FEATURE_LABELS.get(feature, feature)
            raise HTTPException(status_code=403, detail=f"本会场未启用「{label}」")
        return current_user
    return feature_checker
