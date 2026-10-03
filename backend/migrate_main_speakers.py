"""数据库迁移：创建「主发言名单」表 main_speakers

主发言名单独立于动议存在，每个会场一份。新库由 SQLAlchemy 的 create_all
自动建表，此脚本用于补齐已存在的库（别人按文档从零部署时可能漏掉）。

用法：在 backend 目录下执行  python migrate_main_speakers.py
"""
import sqlite3

DB_PATH = "mun_os.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS main_speakers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL REFERENCES committees(id),
        delegation_id INTEGER NOT NULL REFERENCES delegations(id),
        delegate_id INTEGER REFERENCES users(id),
        "order" INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ main_speakers 表已就绪")

# 2. committees 表补 main_unit_duration（主发言名单的单位时长，秒）
c.execute("PRAGMA table_info(committees)")
cols = [row[1] for row in c.fetchall()]
if "main_unit_duration" not in cols:
    c.execute("ALTER TABLE committees ADD COLUMN main_unit_duration INTEGER DEFAULT 60")
    print("✅ committees 已添加 main_unit_duration，默认 60 秒")
else:
    print("ℹ️ committees.main_unit_duration 已存在，跳过")

conn.commit()
conn.close()
print("=== 迁移完成 ===")
