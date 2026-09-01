"""迁移：为 motions 表添加计时器持久化字段"""
import sys
sys.path.insert(0, "/root/mun-os/backend")
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 检查是否已存在
    cols = db.execute(text("PRAGMA table_info(motions)")).fetchall()
    col_names = [c[1] for c in cols]
    
    if "timer_running" not in col_names:
        db.execute(text("ALTER TABLE motions ADD COLUMN timer_running INTEGER DEFAULT 0"))
        print("+ timer_running")
    if "timer_unit_remaining" not in col_names:
        db.execute(text("ALTER TABLE motions ADD COLUMN timer_unit_remaining INTEGER DEFAULT 0"))
        print("+ timer_unit_remaining")
    if "timer_total_remaining" not in col_names:
        db.execute(text("ALTER TABLE motions ADD COLUMN timer_total_remaining INTEGER DEFAULT 0"))
        print("+ timer_total_remaining")
    if "timer_elapsed" not in col_names:
        db.execute(text("ALTER TABLE motions ADD COLUMN timer_elapsed INTEGER DEFAULT 0"))
        print("+ timer_elapsed")
    if "timer_updated_at" not in col_names:
        db.execute(text("ALTER TABLE motions ADD COLUMN timer_updated_at TIMESTAMP"))
        print("+ timer_updated_at")
    
    db.commit()
    print("迁移完成")
except Exception as e:
    print(f"错误: {e}")
    db.rollback()
finally:
    db.close()
