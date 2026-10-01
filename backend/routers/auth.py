from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import LoginRequest, Token
from services import (
    verify_password,
    create_access_token,
    hash_password,
    get_current_user,
    validate_password_strength,
)
from utils.security import login_rate_limiter

router = APIRouter(prefix="/api/auth", tags=["认证"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=Token)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    username = (payload.username or "").strip()
    login_rate_limiter.check(ip, username)

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    login_rate_limiter.reset(ip, username)
    token = create_access_token({"user_id": user.id, "role": user.role})
    return Token(
        access_token=token,
        role=user.role,
        user_id=user.id,
        username=user.username
    )


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=1)


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if data.old_password == data.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    validate_password_strength(data.new_password)
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码修改成功"}
