"""迁移旧版 motion_types 格式到新版"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()
rows = db.execute(text("SELECT id, motion_types FROM committees")).fetchall()
for rid, raw in rows:
    if not raw:
        continue
    old = raw
    new = []
    for item in old:
        if isinstance(item, dict):
            # 旧格式: label, value, needs_topic, needs_unit_duration, needs_total_duration
            if "label" in item:
                new.append({
                    "name": item["label"],
                    "need_speakers_list": item.get("needs_topic", False),
                    "need_unit_duration": item.get("needs_unit_duration", False),
                    "need_total_duration": item.get("needs_total_duration", False),
                    "default_unit_duration": item["default_unit_duration"] if item.get("needs_unit_duration") and item.get("default_unit_duration") else None,
                    "default_total_duration": item["default_total_duration"] if item.get("needs_total_duration") and item.get("default_total_duration") else None,
                })
            else:
                new.append(item)
    val = json.dumps(new, ensure_ascii=False)
    db.execute(text("UPDATE committees SET motion_types = :val WHERE id = :rid"),
               {"val": val, "rid": rid})
    print(f"ID={rid}: {len(old)} types -> {len(new)} types")
db.commit()
db.close()
print("迁移完成")
