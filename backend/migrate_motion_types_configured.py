"""迁移：为 committees 表添加 motion_types_configured 列

用途：区分「从未配置过动议类型」与「配置后删空」。
- 从未配置 -> 前端展示内置默认
- 配置后删空 -> 保持为空（删掉全部内置类型也应生效）

回填策略：已有非空 motion_types 的委员会视为「已配置」；
空列表的保持未配置，行为与迁移前一致（继续展示内置默认）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from sqlalchemy import text, inspect


def run():
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('committees')]

    if 'motion_types_configured' not in columns:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE committees ADD COLUMN motion_types_configured BOOLEAN NOT NULL DEFAULT 0"))
            conn.commit()
        print("已添加 motion_types_configured 列")
    else:
        print("motion_types_configured 列已存在")

    # 回填：非空 motion_types 视为已配置
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, motion_types FROM committees")).fetchall()
        updated = 0
        for cid, raw in rows:
            val = raw
            if isinstance(val, str):
                try:
                    val = json.loads(val) if val else []
                except Exception:
                    val = []
            if val:
                conn.execute(
                    text("UPDATE committees SET motion_types_configured = 1 WHERE id = :cid"),
                    {"cid": cid})
                updated += 1
        conn.commit()
    print(f"已回填 {updated} 个委员会为「已配置」（共 {len(rows)} 个）")


if __name__ == '__main__':
    run()
