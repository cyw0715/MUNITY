"""恢复 HPMUN-1938 和 HPMUN-IMES 的自定义动议类型"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
from sqlalchemy import text
import json

types_1938 = [
    {"name": "陈述", "need_speakers_list": True, "need_unit_duration": True, "need_total_duration": True, "default_unit_duration": 30, "default_total_duration": 120},
    {"name": "辩论", "need_speakers_list": True, "need_unit_duration": False, "need_total_duration": True, "default_unit_duration": None, "default_total_duration": 300},
    {"name": "自由磋商", "need_speakers_list": False, "need_unit_duration": False, "need_total_duration": True, "default_unit_duration": None, "default_total_duration": 600},
    {"name": "文件讨论", "need_speakers_list": True, "need_unit_duration": True, "need_total_duration": True, "default_unit_duration": 60, "default_total_duration": 300},
    {"name": "文件阅读", "need_speakers_list": False, "need_unit_duration": False, "need_total_duration": True, "default_unit_duration": None, "default_total_duration": 600},
    {"name": "开幕致辞", "need_speakers_list": True, "need_unit_duration": True, "need_total_duration": True, "default_unit_duration": 120, "default_total_duration": 600},
]
types_imes = [
    {"name": "轮席发言", "need_speakers_list": True, "need_unit_duration": True, "need_total_duration": True, "default_unit_duration": 60, "default_total_duration": 300},
    {"name": "自由磋商", "need_speakers_list": False, "need_unit_duration": False, "need_total_duration": True, "default_unit_duration": None, "default_total_duration": 600},
    {"name": "多边全体磋商", "need_speakers_list": True, "need_unit_duration": True, "need_total_duration": True, "default_unit_duration": 60, "default_total_duration": 600},
    {"name": "定向双（多）边会谈", "need_speakers_list": False, "need_unit_duration": False, "need_total_duration": True, "default_unit_duration": None, "default_total_duration": 600},
]

db = SessionLocal()
rows = db.execute(text("SELECT id, name FROM committees")).fetchall()
for rid, name in rows:
    if name in ("HPMUN-1938", "HPMUN-1938-BBC"):
        val = json.dumps(types_1938, ensure_ascii=False)
    elif name == "HPMUN-IMES":
        val = json.dumps(types_imes, ensure_ascii=False)
    else:
        # 其他委员会设为空列表
        val = "[]"
    db.execute(text("UPDATE committees SET motion_types = :val WHERE id = :rid"),
               {"val": val, "rid": rid})
    print(f"✅ {name}: motion_types restored")
db.commit()
db.close()
