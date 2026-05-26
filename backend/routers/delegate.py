from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
from database import get_db
from models.user import User
from models.delegation import Delegation
from models.directive import Directive
from models.document import Document
from models.update import Update
from services import require_role
from models.agenda import AgendaItem

router = APIRouter(prefix="/api/delegate", tags=["代表"])
class AgendaItemOut(BaseModel):
    id: int
    committee_id: int
    title: str
    level: int
    order: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


def get_delegate_info(current_user: User) -> tuple:
    """获取代表所属委员会和代表团"""
    if not current_user.delegation_id:
        raise HTTPException(status_code=400, detail="您尚未分配到任何代表团")
    return current_user.delegation_id


# ==================== 提交指令 ====================

class DirectiveCreate(BaseModel):
    drafter: str
    admin_points: int = 0
    secrecy: str = "public"  # public / secret
    content: str = ""
    departments: List[str] = []  # 涉及部门


@router.post("/directives")
def submit_directive(
    data: DirectiveCreate,
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")

    # 验证行政点数
    if data.secrecy == "public" and data.admin_points < 1:
        raise HTTPException(status_code=400, detail="公开指令至少需要1个行政点数")
    if data.secrecy == "secret" and data.admin_points < 2:
        raise HTTPException(status_code=400, detail="秘密指令至少需要2个行政点数")

    # 验证涉及部门
    if not data.departments:
        raise HTTPException(status_code=400, detail="请至少选择一个涉及部门")

    directive = Directive(
        committee_id=delegation.committee_id,
        delegation_id=delegation_id,
        drafter=data.drafter or current_user.username,
        admin_points=data.admin_points,
        secrecy=data.secrecy,
        content=data.content,
        departments=data.departments
    )
    db.add(directive)
    db.commit()
    return {"message": "提交成功"}


@router.get("/directives")
def list_my_directives(current_user: User = Depends(require_role("delegate")), db: Session = Depends(get_db)):
    delegation_id = get_delegate_info(current_user)
    return db.query(Directive).filter(Directive.delegation_id == delegation_id).order_by(Directive.created_at.desc()).all()


# ==================== 提交文件 ====================

class DocumentCreate(BaseModel):
    drafter: str
    doc_type: str  # declaration / memorandum / agreement
    title: str
    content: str = ""
    signing_countries: List[int] = []  # 签署国家（代表团ID列表，协定专用）
    secrecy: str = "public"  # public / secret（协定专用）


@router.post("/documents")
async def submit_document(
    drafter: str = Form(""),
    doc_type: str = Form("declaration"),
    title: str = Form(""),
    content: str = Form(""),
    secrecy: str = Form("public"),
    signing_countries: str = Form("[]"),
    file: UploadFile = File(None),
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")

    # 解析签署国家
    import json
    try:
        signing_countries_list = json.loads(signing_countries)
    except:
        signing_countries_list = []

    # 协定特殊验证
    if doc_type == "agreement":
        # 只有阁首能提交协定
        if not current_user.is_leader:
            raise HTTPException(status_code=403, detail="只有阁首才能提交协定")
        # 协定必须有签署国家
        if not signing_countries_list:
            raise HTTPException(status_code=400, detail="协定必须选择签署国家")

    # 处理文件上传
    file_path = None
    if file and file.filename:
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="只支持 .docx 文件")
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        file_content = await file.read()
        with open(filepath, "wb") as f:
            f.write(file_content)
        file_path = filename

    document = Document(
        committee_id=delegation.committee_id,
        delegation_id=delegation_id,
        drafter=drafter or current_user.username,
        doc_type=doc_type,
        title=title,
        content=content,
        file_path=file_path,
        signing_countries=signing_countries_list if doc_type == "agreement" else None,
        secrecy=secrecy if doc_type == "agreement" else "public"
    )
    db.add(document)
    db.commit()
    return {"message": "提交成功"}


@router.get("/documents")
def list_my_documents(current_user: User = Depends(require_role("delegate")), db: Session = Depends(get_db)):
    delegation_id = get_delegate_info(current_user)
    return db.query(Document).filter(
        Document.delegation_id == delegation_id,
        Document.recalled == False  # 过滤掉已撤回的文件
    ).order_by(Document.created_at.desc()).all()


# ==================== 接收局势更新 ====================

@router.get("/updates")
def list_updates_for_me(
    keyword: str = None,
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """获取局势更新（包括文本和文件类型），支持关键字搜索（包括附件内容）"""
    from utils.file_parser import extract_text_from_file
    
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")

    # 获取所有类型的更新（文本和文件）
    all_updates = db.query(Update).filter(
        Update.committee_id == delegation.committee_id
    ).order_by(Update.created_at.desc()).all()

    result = []
    for u in all_updates:
        if not u.visibility or current_user.id in u.visibility:
            # 如果有关键字，检查是否匹配
            if keyword:
                keyword_lower = keyword.lower()
                title_match = keyword_lower in (u.title or "").lower()
                content_match = keyword_lower in (u.content or "").lower()
                
                # 检查附件内容
                file_content_match = False
                if u.file_path and not (title_match or content_match):
                    file_text = extract_text_from_file(u.file_path)
                    file_content_match = keyword_lower in file_text.lower()
                
                if not (title_match or content_match or file_content_match):
                    continue
            
            result.append({
                "id": u.id,
                "title": u.title,
                "content": u.content,
                "type": u.type,
                "file_path": u.file_path,
                "created_at": u.created_at.isoformat()
            })
    return result


# ==================== 会议文件 ====================

@router.get("/meeting-files")
def list_meeting_files_for_me(
    keyword: str = None,
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """获取会议文件（仅文件类型），支持关键字搜索（包括 docx 附件内容）"""
    from utils.file_parser import extract_text_from_file
    
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")

    # 只获取文件类型的更新
    all_updates = db.query(Update).filter(
        Update.committee_id == delegation.committee_id,
        Update.type == "file"
    ).order_by(Update.created_at.desc()).all()

    result = []
    for u in all_updates:
        if not u.visibility or current_user.id in u.visibility:
            # 如果有关键字，检查是否匹配
            if keyword:
                keyword_lower = keyword.lower()
                title_match = keyword_lower in (u.title or "").lower()
                content_match = keyword_lower in (u.content or "").lower()
                
                # 解析 docx 附件内容
                file_content_match = False
                if u.file_path and not (title_match or content_match):
                    file_text = extract_text_from_file(u.file_path)
                    file_content_match = keyword_lower in file_text.lower()
                
                if not (title_match or content_match or file_content_match):
                    continue
            
            result.append({
                "id": u.id,
                "title": u.title,
                "content": u.content,
                "file_path": u.file_path,
                "created_at": u.created_at.isoformat()
            })
    return result


# ==================== 代表信息 ====================

@router.get("/delegations")
def list_delegations(current_user: User = Depends(require_role("delegate")), db: Session = Depends(get_db)):
    """获取当前委员会的所有代表团（用于签署国家选择）"""
    delegation = db.query(Delegation).filter(Delegation.id == current_user.delegation_id).first()
    if not delegation:
        return []
    return db.query(Delegation).filter(Delegation.committee_id == delegation.committee_id).all()


@router.get("/me")
def get_me(current_user: User = Depends(require_role("delegate")), db: Session = Depends(get_db)):
    delegation = db.query(Delegation).filter(Delegation.id == current_user.delegation_id).first()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "seat": current_user.seat,
        "is_leader": current_user.is_leader,
        "delegation_id": current_user.delegation_id,
        "delegation_name": delegation.name if delegation else None
    }
# ==================== 文件上传/下载 ====================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表上传docx文件"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="只支持 .docx 文件")
    
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")
    
    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # 创建Document记录
    document = Document(
        committee_id=delegation.committee_id,
        delegation_id=delegation_id,
        drafter=current_user.username,
        doc_type="file",
        title=file.filename,
        content="",
        file_path=filename
    )
    db.add(document)
    db.commit()
    
    return {"message": "上传成功", "filename": filename}


@router.get("/download/{filename}")
def download_file(
    filename: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """下载文件（支持 header 和 query parameter 两种认证方式）"""
    # 从 query parameter 或 header 中获取 token
    if token:
        try:
            from jose import jwt
            from config import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="无效的认证凭据")
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role != "delegate":
                raise HTTPException(status_code=403, detail="权限不足")
        except Exception:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
    else:
        raise HTTPException(status_code=401, detail="缺少认证凭据")

    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)


# ==================== 议程查看 ====================

@router.get("/agenda", response_model=List[AgendaItemOut])
def list_agenda(current_user: User = Depends(require_role("delegate")), db: Session = Depends(get_db)):
    """代表查看议程（只读）"""
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")
    return db.query(AgendaItem).filter(
        AgendaItem.committee_id == delegation.committee_id
    ).order_by(AgendaItem.order).all()


# ==================== 代表信息 ====================

# ==================== 时间线查看 ====================

from datetime import timedelta

@router.get("/timeline")
def get_delegate_timeline(
    current_user: User = Depends(require_role("delegate")),
    db: Session = Depends(get_db)
):
    """代表查看当前会议日期"""
    delegation_id = get_delegate_info(current_user)
    delegation = db.query(Delegation).filter(Delegation.id == delegation_id).first()
    if not delegation:
        raise HTTPException(status_code=400, detail="代表团不存在")
    
    from models.timeline import Timeline
    timeline = db.query(Timeline).filter(Timeline.committee_id == delegation.committee_id).first()
    
    if not timeline:
        return {
            "has_timeline": False,
            "conference_date": None,
            "days_per_hour": None,
            "current_date": None
        }
    
    # 计算当前会议日期
    now = datetime.utcnow()
    elapsed_hours = (now - timeline.last_updated).total_seconds() / 3600
    elapsed_days = elapsed_hours * timeline.hours_per_day
    current_date = timeline.conference_date + timedelta(days=elapsed_days)
    
    return {
        "has_timeline": True,
        "conference_date": timeline.conference_date.isoformat(),
        "days_per_hour": timeline.hours_per_day,
        "current_date": current_date.isoformat()
    }
