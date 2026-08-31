"""迁移：为 committees 表添加 motion_types 列"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal
from sqlalchemy import text, inspect

def run():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('committees')]
    if 'motion_types' in columns:
        print("✅ motion_types 列已存在")
        return
    
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE committees ADD COLUMN motion_types TEXT DEFAULT '[]'"))
        conn.commit()
    print("✅ 已添加 motion_types 列")

if __name__ == '__main__':
    run()
