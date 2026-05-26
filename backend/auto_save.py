"""
会议状态自动保存与恢复模块
- 定期保存会议状态到文件
- 启动时自动恢复上次状态
"""
import json
import os
import threading
import time
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_saves")
SAVE_INTERVAL = 30  # 每30秒保存一次

os.makedirs(SAVE_DIR, exist_ok=True)


class AutoSaver:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        """启动自动保存线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._save_loop, daemon=True)
        self._thread.start()
        print("[AutoSave] 自动保存已启动，每30秒保存一次")

    def stop(self):
        """停止自动保存"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _save_loop(self):
        """保存循环"""
        while self._running:
            try:
                time.sleep(SAVE_INTERVAL)
                if self._running:
                    self._save_state()
            except Exception as e:
                print(f"[AutoSave] 保存失败: {e}")

    def _save_state(self):
        """保存当前会议状态"""
        from database import SessionLocal
        from models import Committee, Delegation, User, Motion, SpeakerEntry, RollCall, AgendaItem, Directive, Document, Update, SpeechRecord
        from models.timeline import Timeline
        from models.vote import Vote, VoteRecord

        db = SessionLocal()
        try:
            state = {
                "saved_at": datetime.now().isoformat(),
                "committees": [],
                "delegations": [],
                "users": [],
                "motions": [],
                "speakers": [],
                "rollcall": [],
                "agenda": [],
                "directives": [],
                "documents": [],
                "updates": [],
                "speech_records": [],
                "timelines": [],
                "votes": [],
                "vote_records": []
            }

            # 保存委员会
            for c in db.query(Committee).all():
                state["committees"].append({
                    "id": c.id, "name": c.name, "features": c.features
                })

            # 保存代表团
            for d in db.query(Delegation).all():
                state["delegations"].append({
                    "id": d.id, "name": d.name, "committee_id": d.committee_id
                })

            # 保存用户
            for u in db.query(User).all():
                state["users"].append({
                    "id": u.id, "username": u.username, "password_hash": u.password_hash,
                    "role": u.role, "seat": u.seat, "created_by": u.created_by, "committee_id": u.committee_id,
                    "delegation_id": u.delegation_id, "is_leader": u.is_leader
                })

            # 保存动议
            for m in db.query(Motion).all():
                state["motions"].append({
                    "id": m.id, "committee_id": m.committee_id, "type": m.type,
                    "topic": m.topic, "unit_duration": m.unit_duration,
                    "total_duration": m.total_duration, "status": m.status,
                    "proposer_delegation_id": m.proposer_delegation_id,
                    "proposer_delegate_id": m.proposer_delegate_id
                })

            # 保存发言名单
            for s in db.query(SpeakerEntry).all():
                state["speakers"].append({
                    "id": s.id, "motion_id": s.motion_id, "delegation_id": s.delegation_id,
                    "delegate_id": s.delegate_id, "order": s.order, "has_spoken": s.has_spoken,
                    "duration": s.duration, "content": s.content
                })

            # 保存点名
            for r in db.query(RollCall).all():
                state["rollcall"].append({
                    "id": r.id, "committee_id": r.committee_id, "delegation_id": r.delegation_id,
                    "delegate_id": r.delegate_id, "is_present": r.is_present
                })

            # 保存议程
            for a in db.query(AgendaItem).all():
                state["agenda"].append({
                    "id": a.id, "committee_id": a.committee_id, "title": a.title,
                    "level": a.level, "order": a.order, "is_active": a.is_active
                })

            # 保存指令
            for d in db.query(Directive).all():
                state["directives"].append({
                    "id": d.id, "committee_id": d.committee_id, "delegation_id": d.delegation_id,
                    "drafter": d.drafter, "admin_points": d.admin_points, "secrecy": d.secrecy,
                    "content": d.content, "status": d.status
                })

            # 保存文件
            for d in db.query(Document).all():
                state["documents"].append({
                    "id": d.id, "committee_id": d.committee_id, "delegation_id": d.delegation_id,
                    "drafter": d.drafter, "doc_type": d.doc_type, "title": d.title,
                    "content": d.content, "file_path": d.file_path,
                    "signing_countries": d.signing_countries, "secrecy": d.secrecy
                })

            # 保存局势更新
            for u in db.query(Update).all():
                state["updates"].append({
                    "id": u.id, "committee_id": u.committee_id, "sender_id": u.sender_id,
                    "title": u.title, "content": u.content, "type": u.type,
                    "file_path": u.file_path, "visibility": u.visibility
                })

            # 保存发言记录
            for s in db.query(SpeechRecord).all():
                state["speech_records"].append({
                    "id": s.id, "delegation_id": s.delegation_id, "committee_id": s.committee_id,
                    "motion_id": s.motion_id, "duration": s.duration
                })

            # 保存时间线
            for t in db.query(Timeline).all():
                state["timelines"].append({
                    "id": t.id, "committee_id": t.committee_id,
                    "conference_date": t.conference_date.isoformat() if t.conference_date else None,
                    "hours_per_day": t.hours_per_day,
                    "last_updated": t.last_updated.isoformat() if t.last_updated else None
                })

            # 保存投票
            for v in db.query(Vote).all():
                state["votes"].append({
                    "id": v.id, "committee_id": v.committee_id, "title": v.title,
                    "rule": v.rule, "custom_rule": v.custom_rule,
                    "status": v.status, "veto_enabled": v.veto_enabled,
                    "ended_at": v.ended_at.isoformat() if v.ended_at else None
                })

            # 保存投票记录
            for r in db.query(VoteRecord).all():
                state["vote_records"].append({
                    "id": r.id, "vote_id": r.vote_id, "delegation_id": r.delegation_id,
                    "choice": r.choice, "has_veto": r.has_veto, "is_observer": r.is_observer,
                    "can_vote": r.can_vote, "voted_at": r.voted_at.isoformat() if r.voted_at else None
                })

            # 写入文件
            save_file = os.path.join(SAVE_DIR, "meeting_state.json")
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[AutoSave] 保存失败: {e}")
        finally:
            db.close()

    def restore_state(self):
        """恢复上次保存的状态"""
        save_file = os.path.join(SAVE_DIR, "meeting_state.json")
        if not os.path.exists(save_file):
            print("[AutoSave] 未找到保存文件，跳过恢复")
            return False
        try:
            with open(save_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            print(f"[AutoSave] 找到保存于 {state.get('saved_at', '未知')} 的状态")
            from database import SessionLocal
            from models import Committee, Delegation, User, Motion, SpeakerEntry, RollCall, AgendaItem, Directive, Document, Update, SpeechRecord
            from models.timeline import Timeline
            from models.vote import Vote, VoteRecord

            db = SessionLocal()
            try:
                # 检查数据库是否已有数据
                if db.query(User).count() > 0:
                    print("[AutoSave] 数据库已有数据，跳过恢复")
                    db.close()
                    return False

                # 恢复委员会
                for c in state.get("committees", []):
                    db.add(Committee(id=c["id"], name=c["name"], features=c.get("features")))

                # 恢复代表团
                for d in state.get("delegations", []):
                    db.add(Delegation(id=d["id"], name=d["name"], committee_id=d["committee_id"]))

                # 恢复用户
                for u in state.get("users", []):
                    db.add(User(
                        id=u["id"], username=u["username"], password_hash=u["password_hash"],
                        role=u["role"], seat=u.get("seat"), created_by=u.get("created_by"),
                        committee_id=u.get("committee_id"), delegation_id=u.get("delegation_id"),
                        is_leader=u.get("is_leader", False)
                    ))

                # 恢复动议
                for m in state.get("motions", []):
                    db.add(Motion(
                        id=m["id"], committee_id=m["committee_id"], type=m["type"],
                        topic=m.get("topic"), unit_duration=m.get("unit_duration"),
                        total_duration=m.get("total_duration"), status=m.get("status", "pending"),
                        proposer_delegation_id=m.get("proposer_delegation_id"),
                        proposer_delegate_id=m.get("proposer_delegate_id")
                    ))

                # 恢复发言名单
                for s in state.get("speakers", []):
                    db.add(SpeakerEntry(
                        id=s["id"], motion_id=s["motion_id"], delegation_id=s["delegation_id"],
                        delegate_id=s.get("delegate_id"), order=s.get("order", 0),
                        has_spoken=s.get("has_spoken", 0), duration=s.get("duration", 0),
                        content=s.get("content")
                    ))

                # 恢复点名
                for r in state.get("rollcall", []):
                    db.add(RollCall(
                        id=r.get("id"), committee_id=r["committee_id"], delegation_id=r["delegation_id"],
                        delegate_id=r.get("delegate_id"), is_present=r.get("is_present", False)
                    ))

                # 恢复议程
                for a in state.get("agenda", []):
                    db.add(AgendaItem(
                        id=a["id"], committee_id=a["committee_id"], title=a["title"],
                        level=a.get("level", 1), order=a.get("order", 0),
                        is_active=a.get("is_active", False)
                    ))

                # 恢复指令
                for d in state.get("directives", []):
                    db.add(Directive(
                        id=d["id"], committee_id=d["committee_id"], delegation_id=d["delegation_id"],
                        drafter=d["drafter"], admin_points=d.get("admin_points", 0),
                        secrecy=d.get("secrecy", "public"), content=d.get("content"),
                        status=d.get("status", "unread")
                    ))

                # 恢复文件
                for d in state.get("documents", []):
                    db.add(Document(
                        id=d["id"], committee_id=d["committee_id"], delegation_id=d["delegation_id"],
                        drafter=d["drafter"], doc_type=d["doc_type"], title=d["title"],
                        content=d.get("content"), file_path=d.get("file_path"),
                        signing_countries=d.get("signing_countries"), secrecy=d.get("secrecy", "public")
                    ))

                # 恢复局势更新
                for u in state.get("updates", []):
                    db.add(Update(
                        id=u["id"], committee_id=u["committee_id"], sender_id=u["sender_id"],
                        title=u["title"], content=u.get("content"), type=u.get("type", "text"),
                        file_path=u.get("file_path"), visibility=u.get("visibility", [])
                    ))

                # 恢复发言记录
                for s in state.get("speech_records", []):
                    db.add(SpeechRecord(
                        id=s.get("id"), delegation_id=s["delegation_id"], committee_id=s["committee_id"],
                        motion_id=s.get("motion_id"), duration=s.get("duration", 0)
                    ))
                # 恢复时间线
                for t in state.get("timelines", []):
                    from datetime import date as date_type
                    conf_date = None
                    if t.get("conference_date"):
                        try:
                            conf_date = date_type.fromisoformat(t["conference_date"])
                        except (ValueError, TypeError):
                            pass
                    db.add(Timeline(
                        id=t["id"], committee_id=t["committee_id"],
                        conference_date=conf_date,
                        hours_per_day=t.get("hours_per_day", 1.0)
                    ))

                # 恢复投票
                for v in state.get("votes", []):
                    ended_at = None
                    if v.get("ended_at"):
                        try:
                            ended_at = datetime.fromisoformat(v["ended_at"])
                        except (ValueError, TypeError):
                            pass
                    db.add(Vote(
                        id=v["id"], committee_id=v["committee_id"], title=v["title"],
                        rule=v.get("rule", "qualified_majority"), custom_rule=v.get("custom_rule"),
                        status=v.get("status", "pending"), veto_enabled=v.get("veto_enabled", False),
                        ended_at=ended_at
                    ))

                # 恢复投票记录
                for r in state.get("vote_records", []):
                    voted_at = None
                    if r.get("voted_at"):
                        try:
                            voted_at = datetime.fromisoformat(r["voted_at"])
                        except (ValueError, TypeError):
                            pass
                    db.add(VoteRecord(
                        id=r["id"], vote_id=r["vote_id"], delegation_id=r["delegation_id"],
                        choice=r.get("choice"), has_veto=r.get("has_veto", False),
                        is_observer=r.get("is_observer", False), can_vote=r.get("can_vote", True),
                        voted_at=voted_at
                    ))

                db.commit()
                print("[AutoSave] 状态恢复成功")
                return True

            except Exception as e:
                db.rollback()
                print(f"[AutoSave] 恢复失败: {e}")
                return False
            finally:
                db.close()

        except Exception as e:
            print(f"[AutoSave] 读取保存文件失败: {e}")
            return False


# 全局实例
auto_saver = AutoSaver()
