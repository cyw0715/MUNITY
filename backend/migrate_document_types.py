"""迁移：文件类型配置

新增列：
- committees.document_types          文件类型完整列表（内置 + 自定义）
- committees.document_types_configured  区分「从未配置」与「配置后删空」
- documents.departments              涉及部门（按文件类型配置决定是否启用）

回填：不设默认类型，全部委员会保持「未配置」状态，
即继续使用内置默认（声明/备忘录/协定），与迁移前行为一致。
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

    _add_column(inspector, "committees", "document_types", "document_types TEXT DEFAULT '[]'")
    _add_column(inspector, "committees", "document_types_configured",
                "document_types_configured BOOLEAN NOT NULL DEFAULT 0")
    _add_column(inspector, "documents", "departments", "departments TEXT")

    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM committees")).scalar()
        configured = conn.execute(
            text("SELECT COUNT(*) FROM committees WHERE document_types_configured = 1")).scalar()
    print(f"committee 共 {n} 个，其中已配置文件类型 {configured} 个（其余使用内置默认）")


if __name__ == '__main__':
    run()
