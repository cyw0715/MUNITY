"""迁移：委员会侧边栏品牌字段

新增列：
- committees.logo_icon      徽标文字（1–2 字符，可为 emoji）
- committees.logo_image     上传的图标文件名
- committees.display_title  侧边栏标题

不回填：三列均为 NULL 时，前端沿用默认「M」徽标与「MUNITY OS」标题，
与迁移前行为一致。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from sqlalchemy import text, inspect


def _add_column(inspector, table: str, column: str, ddl: str):
    cols = [c['name'] for c in inspector.get_columns(table)]
    if column in cols:
        print(f"{table}.{column} 列已存在")
        return
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
        conn.commit()
    print(f"已添加 {table}.{column}")


def run():
    inspector = inspect(engine)
    _add_column(inspector, "committees", "logo_icon", "logo_icon VARCHAR(16)")
    _add_column(inspector, "committees", "logo_image", "logo_image VARCHAR(255)")
    _add_column(inspector, "committees", "display_title", "display_title VARCHAR(100)")

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM committees")).scalar()
        configured = conn.execute(
            text("SELECT COUNT(*) FROM committees WHERE logo_icon IS NOT NULL "
                 "OR logo_image IS NOT NULL OR display_title IS NOT NULL")).scalar()
    print(f"committee 共 {n} 个，其中已设置品牌 {configured} 个（其余沿用默认）")


if __name__ == '__main__':
    run()
