from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from database import get_db
from models.user import User
from models.delegation import Delegation
from models.vote import Vote, VoteRecord
from services import require_role

router = APIRouter(prefix="/api/staff", tags=["学团-投票表决"])


def get_staff_committee(current_user: User) -> int:
    """获取学团所属委员会"""
    if not current_user.committee_id:
        raise HTTPException(status_code=400, detail="您尚未分配到任何委员会")
    return current_user.committee_id


# ==================== 投票管理 ====================

class VoteCreate(BaseModel):
    title: str
    rule: str = "qualified_majority"  # qualified_majority / simple_majority / custom
    custom_rule: Optional[dict] = None
    veto_enabled: bool = False
    excluded_delegations: List[int] = []  # 不参与投票的代表团ID（观察员等）
    veto_delegations: List[int] = []  # 拥有一票否决权的代表团ID


@router.post("/votes")
def create_vote(
    data: VoteCreate,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """创建投票"""
    committee_id = get_staff_committee(current_user)

    # 检查是否有正在进行的投票
    active_vote = db.query(Vote).filter(
        Vote.committee_id == committee_id,
        Vote.status.in_(["pending", "voting"])
    ).first()
    if active_vote:
        raise HTTPException(status_code=400, detail="已有正在进行的投票，请先结束")

    # 获取该委员会的所有代表团
    delegations = db.query(Delegation).filter(Delegation.committee_id == committee_id).all()
    if not delegations:
        raise HTTPException(status_code=400, detail="没有代表团，无法进行投票")

    # 创建投票
    vote = Vote(
        committee_id=committee_id,
        title=data.title,
        rule=data.rule,
        custom_rule=data.custom_rule,
        veto_enabled=data.veto_enabled,
        status="pending"
    )
    db.add(vote)
    db.flush()

    # 为每个代表团创建投票记录
    for d in delegations:
        record = VoteRecord(
            vote_id=vote.id,
            delegation_id=d.id,
            has_veto=d.id in data.veto_delegations,
            is_observer=d.id in data.excluded_delegations,
            can_vote=d.id not in data.excluded_delegations
        )
        db.add(record)

    db.commit()
    return {"message": "投票创建成功", "vote_id": vote.id}


@router.get("/votes")
def list_votes(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取投票列表"""
    committee_id = get_staff_committee(current_user)
    votes = db.query(Vote).filter(Vote.committee_id == committee_id).order_by(Vote.created_at.desc()).all()

    result = []
    for v in votes:
        records = db.query(VoteRecord).filter(VoteRecord.vote_id == v.id).all()
        total = len(records)
        voted = len([r for r in records if r.choice])
        yes_count = len([r for r in records if r.choice == "yes"])
        no_count = len([r for r in records if r.choice == "no"])
        abstain_count = len([r for r in records if r.choice == "abstain"])
        can_vote_count = len([r for r in records if r.can_vote])

        result.append({
            "id": v.id,
            "title": v.title,
            "rule": v.rule,
            "custom_rule": v.custom_rule,
            "status": v.status,
            "veto_enabled": v.veto_enabled,
            "total": total,
            "voted": voted,
            "can_vote": can_vote_count,
            "yes_count": yes_count,
            "no_count": no_count,
            "abstain_count": abstain_count,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "ended_at": v.ended_at.isoformat() if v.ended_at else None
        })
    return result


@router.get("/votes/{vote_id}")
def get_vote_detail(
    vote_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """获取投票详情"""
    committee_id = get_staff_committee(current_user)
    vote = db.query(Vote).filter(Vote.id == vote_id, Vote.committee_id == committee_id).first()
    if not vote:
        raise HTTPException(status_code=404, detail="投票不存在")

    records = db.query(VoteRecord).filter(VoteRecord.vote_id == vote_id).all()
    delegations = db.query(Delegation).filter(Delegation.committee_id == committee_id).all()

    delegation_map = {d.id: d.name for d in delegations}

    record_list = []
    for r in records:
        record_list.append({
            "id": r.id,
            "delegation_id": r.delegation_id,
            "delegation_name": delegation_map.get(r.delegation_id, "未知"),
            "choice": r.choice,
            "has_veto": r.has_veto,
            "is_observer": r.is_observer,
            "can_vote": r.can_vote,
            "voted_at": r.voted_at.isoformat() if r.voted_at else None
        })

    return {
        "id": vote.id,
        "title": vote.title,
        "rule": vote.rule,
        "custom_rule": vote.custom_rule,
        "status": vote.status,
        "veto_enabled": vote.veto_enabled,
        "records": record_list,
        "created_at": vote.created_at.isoformat() if vote.created_at else None,
        "ended_at": vote.ended_at.isoformat() if vote.ended_at else None
    }


@router.put("/votes/{vote_id}/start")
def start_vote(
    vote_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """开始投票"""
    committee_id = get_staff_committee(current_user)
    vote = db.query(Vote).filter(Vote.id == vote_id, Vote.committee_id == committee_id).first()
    if not vote:
        raise HTTPException(status_code=404, detail="投票不存在")
    if vote.status != "pending":
        raise HTTPException(status_code=400, detail="投票状态不正确")

    vote.status = "voting"
    db.commit()
    return {"message": "投票已开始"}


@router.put("/votes/{vote_id}/vote")
def submit_vote(
    vote_id: int,
    delegation_id: int,
    choice: str,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """记录投票（学团代表代表投票）"""
    committee_id = get_staff_committee(current_user)
    vote = db.query(Vote).filter(Vote.id == vote_id, Vote.committee_id == committee_id).first()
    if not vote:
        raise HTTPException(status_code=404, detail="投票不存在")
    if vote.status != "voting":
        raise HTTPException(status_code=400, detail="投票未在进行中")

    if choice not in ["yes", "no", "abstain"]:
        raise HTTPException(status_code=400, detail="无效的投票选择")

    record = db.query(VoteRecord).filter(
        VoteRecord.vote_id == vote_id,
        VoteRecord.delegation_id == delegation_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="投票记录不存在")
    if not record.can_vote:
        raise HTTPException(status_code=400, detail="该代表团不能投票")

    record.choice = choice
    record.voted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "投票成功"}


@router.put("/votes/{vote_id}/end")
def end_vote(
    vote_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """结束投票并计算结果"""
    committee_id = get_staff_committee(current_user)
    vote = db.query(Vote).filter(Vote.id == vote_id, Vote.committee_id == committee_id).first()
    if not vote:
        raise HTTPException(status_code=404, detail="投票不存在")
    if vote.status != "voting":
        raise HTTPException(status_code=400, detail="投票未在进行中")

    records = db.query(VoteRecord).filter(VoteRecord.vote_id == vote_id).all()

    # 计算投票结果
    can_vote_records = [r for r in records if r.can_vote]
    yes_count = len([r for r in can_vote_records if r.choice == "yes"])
    no_count = len([r for r in can_vote_records if r.choice == "no"])
    abstain_count = len([r for r in can_vote_records if r.choice == "abstain"])
    total_can_vote = len(can_vote_records)

    # 检查一票否决
    veto_rejected = False
    if vote.veto_enabled:
        veto_records = [r for r in can_vote_records if r.has_veto and r.choice == "no"]
        if veto_records:
            veto_rejected = True

    # 根据规则判断是否通过
    passed = False
    if not veto_rejected:
        if vote.rule == "qualified_majority":
            # 绝对多数：2/3赞成，且弃权不过半
            if total_can_vote > 0:
                yes_ratio = yes_count / total_can_vote
                abstain_ratio = abstain_count / total_can_vote
                passed = yes_ratio >= 2/3 and abstain_ratio <= 0.5
        elif vote.rule == "simple_majority":
            # 简单多数：赞成 > 反对
            passed = yes_count > no_count
        elif vote.rule == "custom" and vote.custom_rule:
            # 自定义规则
            threshold = vote.custom_rule.get("threshold", 0.5)
            if total_can_vote > 0:
                yes_ratio = yes_count / total_can_vote
                passed = yes_ratio >= threshold

    vote.status = "passed" if passed else "failed"
    vote.ended_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "投票已结束",
        "passed": passed,
        "veto_rejected": veto_rejected,
        "yes": yes_count,
        "no": no_count,
        "abstain": abstain_count,
        "total": total_can_vote
    }


@router.delete("/votes/{vote_id}")
def delete_vote(
    vote_id: int,
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db)
):
    """删除投票"""
    committee_id = get_staff_committee(current_user)
    vote = db.query(Vote).filter(Vote.id == vote_id, Vote.committee_id == committee_id).first()
    if not vote:
        raise HTTPException(status_code=404, detail="投票不存在")

    db.delete(vote)
    db.commit()
    return {"message": "删除成功"}
