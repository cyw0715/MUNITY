"""安全相关工具：路径清洗、上传校验、登录限流。"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, UploadFile

from config import (
    ALLOWED_UPLOAD_EXTENSIONS,
    LOGIN_LOCKOUT_SECONDS,
    LOGIN_RATE_LIMIT_PER_MINUTE,
    MAX_UPLOAD_BYTES,
)

# 文件名安全校验：只排除控制字符与路径分隔符。
# 中文标点（如「、」U+3001）、全角符号、空格等都是合法文件名字符；早先只放行
# 汉字 U+4E00-9FFF，使得「联合王国、奥地利帝国…协定.docx」这类文件在下载时
# 被判「非法文件名」（400），尽管文件就在磁盘上。
# 路径穿越已由下面的分隔符检查、basename 相等检查与 base_dir 包含性检查兜底。
_SAFE_NAME_RE = re.compile(r"^[^\x00-\x1f\x7f/\\]+$")


def safe_join(base_dir: str, filename: str) -> str:
    """将用户可控的 filename 安全地限制在 base_dir 内，否则 400。"""
    if not filename or filename in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名")

    # 拒绝路径分隔符与空字节
    if "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="非法文件名")

    name = os.path.basename(filename)
    if name != filename or name in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名")

    if not _SAFE_NAME_RE.match(name):
        raise HTTPException(status_code=400, detail="非法文件名")

    base = os.path.abspath(base_dir)
    filepath = os.path.abspath(os.path.join(base, name))
    if not filepath.startswith(base + os.sep) and filepath != base:
        raise HTTPException(status_code=400, detail="非法文件名")
    return filepath


def original_display_name(stored_name: str) -> str:
    """从 `{uuid32}_{original}` 还原展示名；失败则返回原名。"""
    if "_" in stored_name:
        prefix, rest = stored_name.split("_", 1)
        if len(prefix) == 32 and rest:
            return rest
    return stored_name


async def save_upload_safely(file: UploadFile, upload_dir: str, uuid_hex: str) -> str:
    """校验并保存上传文件，返回存储文件名 `{uuid}_{safe_original}`。"""
    raw_name = file.filename or ""
    if not raw_name:
        raise HTTPException(status_code=400, detail="缺少文件名")

    display = os.path.basename(raw_name.replace("\\", "/"))
    ext = os.path.splitext(display)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="只支持 .docx 文件")

    # 防御：清理原始名中的危险字符后再拼接（只替换控制字符与路径分隔符，
    # 保留中文标点，否则存下来的名字会对不上前端展示、也与下载校验不一致）
    safe_display = re.sub(r"[\x00-\x1f\x7f/\\]", "_", display)
    if not safe_display or safe_display in (".", ".."):
        raise HTTPException(status_code=400, detail="非法文件名")

    stored = f"{uuid_hex}_{safe_display}"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = safe_join(upload_dir, stored)

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"文件超过大小限制（{MAX_UPLOAD_BYTES // (1024 * 1024)}MB）")
    if len(content) < 4 or content[:2] != b"PK":
        raise HTTPException(status_code=400, detail="文件不是有效的 .docx（ZIP）文档")

    with open(filepath, "wb") as f:
        f.write(content)
    return stored


class LoginRateLimiter:
    """按 (ip, username) 维度的简单内存限流。"""

    def __init__(self, limit_per_minute: int, lockout_seconds: int):
        self.limit = limit_per_minute
        self.lockout_seconds = lockout_seconds
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._locked_until: Dict[Tuple[str, str], float] = {}

    def check(self, ip: str, username: str) -> None:
        key = (ip or "-", (username or "").lower())
        now = time.time()

        until = self._locked_until.get(key)
        if until and now < until:
            retry_in = int(until - now)
            raise HTTPException(
                status_code=429,
                detail=f"尝试过于频繁，请 {retry_in} 秒后再试",
            )

        q = self._hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.limit:
            self._locked_until[key] = now + self.lockout_seconds
            self._hits[key] = deque()
            raise HTTPException(
                status_code=429,
                detail=f"尝试过于频繁，请 {self.lockout_seconds} 秒后再试",
            )
        q.append(now)

    def reset(self, ip: str, username: str) -> None:
        key = (ip or "-", (username or "").lower())
        self._hits.pop(key, None)
        self._locked_until.pop(key, None)


login_rate_limiter = LoginRateLimiter(LOGIN_RATE_LIMIT_PER_MINUTE, LOGIN_LOCKOUT_SECONDS)
