"""委员会侧边栏图标：上传、删除、路径解析。

图标是可直接访问的静态资源，故校验比文档上传更严：
扩展名白名单（不含 svg）+ 大小上限 + 文件头魔数比对，
避免把改名的可执行内容当成图片直出。
"""
from __future__ import annotations

import os
import re
import uuid

from fastapi import HTTPException, UploadFile

from config import ALLOWED_LOGO_EXTENSIONS, MAX_LOGO_BYTES
from utils.security import safe_join

LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "logos")

# 各格式文件头
_MAGIC = (
    (b"\x89PNG\r\n\x1a\n", {".png"}),
    (b"\xff\xd8\xff", {".jpg", ".jpeg"}),
    (b"GIF87a", {".gif"}),
    (b"GIF89a", {".gif"}),
)


def _matches_magic(content: bytes, ext: str) -> bool:
    if ext == ".webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    for magic, exts in _MAGIC:
        if ext in exts and content.startswith(magic):
            return True
    return False


async def save_logo(file: UploadFile, uuid_hex: str | None = None) -> str:
    """校验并保存图标，返回存储文件名。"""
    raw_name = file.filename or ""
    display = os.path.basename(raw_name.replace("\\", "/"))
    ext = os.path.splitext(display)[1].lower()
    if ext not in ALLOWED_LOGO_EXTENSIONS:
        allowed = "、".join(sorted(ALLOWED_LOGO_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"图标只支持 {allowed} 格式")

    content = await file.read(MAX_LOGO_BYTES + 1)
    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=413,
                            detail=f"图标超过大小限制（{MAX_LOGO_BYTES // (1024 * 1024)}MB）")
    if len(content) < 12 or not _matches_magic(content, ext):
        raise HTTPException(status_code=400, detail="文件内容不是有效的图片")

    stored = f"{(uuid_hex or uuid.uuid4().hex)}{ext}"
    os.makedirs(LOGO_DIR, exist_ok=True)
    filepath = safe_join(LOGO_DIR, stored)
    with open(filepath, "wb") as f:
        f.write(content)
    return stored


def logo_path(stored_name: str | None) -> str | None:
    """存储名 -> 绝对路径；文件不存在或名字非法时返回 None。"""
    if not stored_name:
        return None
    try:
        path = safe_join(LOGO_DIR, stored_name)
    except HTTPException:
        return None
    return path if os.path.isfile(path) else None


def delete_logo_file(stored_name: str | None) -> None:
    """删除图标文件；失败不影响主流程（如文件已被替换或不存在）。"""
    path = logo_path(stored_name)
    if not path:
        return
    try:
        os.remove(path)
    except OSError:
        pass
