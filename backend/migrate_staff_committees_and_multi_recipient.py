"""
数据库迁移脚本：
1. 创建 staff_committees 关联表（学团多委员会）
2. 修改 async_messages 表：receiver_id/receiver_delegation_id 改为 JSON 数组
"""
import sqlite3
import json

DB_PATH = "mun_os.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== 迁移开始 ===")

# 1. 创建 staff_committees 表
c.execute("""
    CREATE TABLE IF NOT EXISTS staff_committees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER NOT NULL REFERENCES users(id),
        committee_id INTEGER NOT NULL REFERENCES committees(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(staff_id, committee_id)
    )
""")
print("✅ staff_committees 表已创建")

# 2. 将已有 committee_id 的 staff 迁移到 staff_committees
c.execute("SELECT id, committee_id FROM users WHERE role='staff' AND committee_id IS NOT NULL")
existing = c.fetchall()
for staff_id, committee_id in existing:
    c.execute(
        "INSERT OR IGNORE INTO staff_committees (staff_id, committee_id) VALUES (?, ?)",
        (staff_id, committee_id)
    )
print(f"✅ 已迁移 {len(existing)} 个学团的委员会关联")

# 3. 修改 async_messages 表：添加 JSON 数组字段
# 先检查列是否存在
c.execute("PRAGMA table_info(async_messages)")
columns = [col[1] for col in c.fetchall()]

if 'receiver_ids' not in columns:
    c.execute("ALTER TABLE async_messages ADD COLUMN receiver_ids TEXT DEFAULT '[]'")
    c.execute("ALTER TABLE async_messages ADD COLUMN receiver_delegation_ids TEXT DEFAULT '[]'")
    print("✅ async_messages 已添加 receiver_ids / receiver_delegation_ids 字段")
    
    # 迁移现有数据：将单值转为 JSON 数组
    c.execute("SELECT id, receiver_id, receiver_delegation_id FROM async_messages WHERE receiver_id IS NOT NULL OR receiver_delegation_id IS NOT NULL")
    existing_msgs = c.fetchall()
    for msg_id, rid, d_id in existing_msgs:
        r_ids = json.dumps([rid]) if rid else '[]'
        d_ids = json.dumps([d_id]) if d_id else '[]'
        c.execute("UPDATE async_messages SET receiver_ids=?, receiver_delegation_ids=? WHERE id=?", 
                  (r_ids, d_ids, msg_id))
    print(f"✅ 已迁移 {len(existing_msgs)} 条消息的接收者字段")
else:
    print("ℹ️ receiver_ids/receiver_delegation_ids 字段已存在，跳过")

# 4. 修改 async_messages 表的 is_read 为 TEXT（JSON 存储多个接收者的已读状态）
# 改为存读状态数组 [{"user_id": 1, "is_read": true, "read_at": "..."}, ...]
if 'read_by' not in columns:
    c.execute("ALTER TABLE async_messages ADD COLUMN read_by TEXT DEFAULT '[]'")
    print("✅ async_messages 已添加 read_by 字段")
else:
    print("ℹ️ read_by 字段已存在")

conn.commit()
conn.close()
print("=== 迁移完成 ===")
