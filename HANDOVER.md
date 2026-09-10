# MUNITY 平台交接文档

> 交接日期：2026-09-10
> 本地仓库：`/mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade`
> GitHub：`github.com/cyw0715/MUNITY`（分支 `main`）
> 线上域名：`munityos.cn`
> ECS 服务器：47.116.65.0

---

## 一、项目架构总览

```
MUNITY/
├── backend/               # FastAPI + SQLAlchemy + SQLite
│   ├── main.py            # 入口，注册路由、启动事件
│   ├── database.py        # SQLAlchemy engine/session
│   ├── config.py          # 配置（SECRET_KEY 等）
│   ├── models/            # 数据模型
│   │   ├── user.py        # User
│   │   ├── committee.py   # Committee
│   │   ├── delegation.py  # Delegation
│   │   ├── motion.py      # Motion, SpeakerEntry
│   │   ├── directive.py   # 指令
│   │   ├── document.py    # 文件（含联署字段）
│   │   └── update.py      # 局势更新
│   ├── routers/           # API 路由
│   │   ├── auth.py        # 登录/JWT
│   │   ├── delegate.py    # 代表端 API
│   │   ├── staff.py       # 学团端 API
│   │   └── ...
│   ├── services/
│   │   └── websocket_manager.py  # WS 管理器（全局单例）
│   ├── schemas/           # Pydantic 模型
│   └── utils/             # 工具函数
├── frontend/              # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── views/delegate/   # 代表端页面
│   │   ├── views/staff/      # 学团端页面
│   │   └── services/         # API 调用、WebSocket
│   ├── dist/              # 构建产物（本地）
│   └── .env               # 环境变量（本地）
└── deploy/                # 部署脚本（仅供参考，实际已手动部署）
```

---

## 二、产物存放规则（关键！）

### 2.1 线上产物路径一览

| 组件 | 服务器路径 | 来源 |
|------|-----------|------|
| **后端代码** | `/root/mun-os/backend/` | WSL `scp` 推送 |
| **数据库** | `/root/mun-os/backend/mun_os.db` | SQLite（自动生成或重建） |
| **前端静态文件** | `/var/www/munity/` | WSL `npm run build` → `tar.gz` → SSH 解压 |
| **nginx 静态文件配置** | `root /var/www/munity;` | nginx 配置 |
| **systemd 服务** | `/etc/systemd/system/mun-os.service` | systemd 管理 |
| **nginx 配置** | `/etc/nginx/sites-available/munity` | 手动编辑（备份在 `.bak.20260909203533`） |

### 2.2 前端部署流程（完整命令）

**本地 WSL：**
```bash
# 1. 前端构建（确保后端修改也一起提交）
cd /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/frontend
npm run build

# 2. 打包
tar czf /tmp/munity-frontend.tar.gz -C dist/ .

# 3. 部署到 ECS（先清空再解压）
cat /tmp/munity-frontend.tar.gz | ssh root@47.116.65.0 "\
  rm -rf /var/www/munity/assets/* \
         /var/www/munity/favicon.svg \
         /var/www/munity/icons.svg \
         /var/www/munity/index.html \
  && tar xzf - -C /var/www/munity/"
```

### 2.3 后端部署流程

```bash
# 复制后端代码到 ECS
scp /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/backend/routers/delegate.py \
    root@47.116.65.0:/root/mun-os/backend/routers/delegate.py

# 重启后端
ssh root@47.116.65.0 "systemctl restart mun-os.service"

# 验证新进程运行
ssh root@47.116.65.0 "ps aux | grep uvicorn | grep -v grep"
```

### 2.4 完整部署流程（一次性跑完）

```bash
# 在 WSL 中执行
cd /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade

# Step 1: 构建前端
cd frontend && npm run build && cd ..

# Step 2: 打包前端
tar czf /tmp/munity-frontend.tar.gz -C frontend/dist/ .

# Step 3: 前端部署到 ECS
cat /tmp/munity-frontend.tar.gz | ssh root@47.116.65.0 "\
  rm -rf /var/www/munity/assets/* \
         /var/www/munity/favicon.svg \
         /var/www/munity/icons.svg \
         /var/www/munity/index.html \
  && tar xzf - -C /var/www/munity/"

# Step 4: 部署修改过的后端文件（按需替换）
# scp backend/routers/delegate.py root@47.116.65.0:/root/mun-os/backend/routers/
# scp backend/routers/staff.py root@47.116.65.0:/root/mun-os/backend/routers/

# Step 5: 重启后端
ssh root@47.116.65.0 "systemctl restart mun-os.service"

# Step 6: 验证
ssh root@47.116.65.0 "ps aux | grep uvicorn | grep -v grep"

# Step 7: 提交 GitHub
git add -A && git commit -m "..." && git push

# Step 8: 清理临时文件
rm -f /tmp/munity-frontend.tar.gz
```

### 2.5 验证部署一致性

```bash
# 方法：对比 md5
# 本地：
find frontend/dist/ -type f -exec md5sum {} \;

# 远程（通过 SSH 执行相同范围的 md5sum）
ssh root@47.116.65.0 "find /var/www/munity/ -type f -exec md5sum {} \;"

# 后端
md5sum backend/routers/delegate.py
ssh root@47.116.65.0 "md5sum /root/mun-os/backend/routers/delegate.py"
```

### 2.6 工作目录产物

| 路径 | 用途 |
|------|------|
| `E:\Chenyuewei\MUN\2026-08-30-munity-upgrade\` | WSL 映射 `/mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade` — **主工作目录** |
| `frontend/dist/` | 前端构建产物（`.gitignore`，无需 commit） |
| `backend/` | 后端源码（Git 跟踪） |
| `backend/uploads/` | 上传文件（`.gitignore`） |
| `backend/auto_saves/` | 会议状态自动存档（`.gitignore`） |

---

## 三、ECS 服务器配置

### 3.1 服务管理

```bash
# systemd 服务（重要！）
# 服务名：mun-os.service
# 配置文件：/etc/systemd/system/mun-os.service

# 常用命令
systemctl status mun-os.service     # 查看状态
systemctl restart mun-os.service    # 重启后端
systemctl stop mun-os.service       # 停止后端
journalctl -u mun-os.service -n 50  # 查看日志（最近50行）
journalctl -u mun-os.service -f    # 跟踪日志

# ⚠️ 不要用 pkill！systemd 有 Restart=always，pkill 后 systemd 会恢复旧进程。
# 重启必须用 systemctl restart。
```

### 3.2 nginx 配置

**⚠️ 当前问题（2026-09-10）：nginx 配置被覆盖**

部署脚本写入了只有 HTTP 80 的简化配置（root 指向 `/home/deploy/mun-os/frontend/dist`），导致：
- HTTPS（443）丢失
- WebSocket 代理（`/ws/`、`/api/ws/`）丢失
- 前端 root 指向错误的路径

**修复方法：**

```bash
# 恢复备份的完整配置（含 SSL + WS + 登录限流）
cp /etc/nginx/sites-available/munity.bak.20260909203533 \
   /etc/nginx/sites-available/munity

# 测试并重载
nginx -t && systemctl reload nginx

# 验证 HTTPS 恢复
curl -I https://munityos.cn
```

### 3.3 数据库

- 路径：`/root/mun-os/backend/mun_os.db`
- 类型：SQLite（WAL 模式）
- 管理：通过后端 API 读写，**不要直接 SQL 写入绕过后端逻辑**
- 备份建议：`cp mun_os.db mun_os.db.$(date +%Y%m%d).bak`
- ⚠️ **2026-09-04 发生过数据库文件丢失**（原因未完全确定，可能是 `os.remove` 误操作）。建议定期备份。

### 3.4 日志

```bash
# 后端日志
journalctl -u mun-os.service -n 50 --no-pager

# nginx 访问日志
tail -n 50 /var/log/nginx/access.log

# nginx 错误日志
tail -n 50 /var/log/nginx/error.log
```

---

## 四、WebSocket 实时同步机制

### 4.1 架构

```
代表端/学团端 → wss://munityos.cn/api/ws/?token=xxx
                              ↓
                     nginx proxy_pass
                              ↓
                    FastAPI (port 8000)
                              ↓
                   WebSocketManager (内存)
                   ┌─────────────────────┐
                   │ active_connections   │  { user_id: [WebSocket, ...] }
                   │ user_committees      │  { user_id: set(committee_ids) }
                   └─────────────────────┘
                              ↓
                   独立 try/except (每个推送)
```

### 4.2 关键约束

- **内存状态**：`ws_manager` 是全局单例，所有在线连接保存在内存中。重启后端后所有 WS 连接断开，前端自动重连（5s 间隔）。
- **跨进程问题**：`uvicorn --workers N`（N≥2）会导致每个 worker 有独立 `ws_manager`，广播无法跨进程。**必须 `--workers 1`**。
- **异常处理**：每个 `ws_manager.send_to_*` 调用必须包裹独立 `try/except`，避免一个推送失败跳过后续代码（2026-09-03 修复）。
- **兜底轮询**：前端 WS 监听的同时，部分场景（如文件联署）还有 30s `setInterval` 轮询作为兜底。

### 4.3 事件类型

| 事件 | 推送范围 | 描述 |
|------|---------|------|
| `documents_changed` | 委员会全体 + 学团 | 文件增删改后广播 |
| `endorsement_new` | 联署代表团阁首 | 新联署请求 |
| `endorsement_reviewed` | 提交方代表团 | 联署审批结果 |
| `endorsement_completed` | **仅学团端** | 联署全部完成（2026-09-03 修复：不对代表开放） |
| `updates_changed` | 委员会全体 | 局势更新变动 |
| `agenda_changed` | 委员会全体 | 议程变更 |
| `roll_call_changed` | 委员会全体 | 点名变更 |
| `timer_state` | 委员会全体 | 计时器状态同步 |

---

## 五、关键业务逻辑

### 5.1 联署文件系统

**流程：**
```
非阁首代表提交 → 自动将本代表团加入联署名单首位
                → 所有联署代表团阁首收到通知
                → 各阁首审批（通过/拒绝）
                → 全部通过 → 学团可发布
                → 任一拒绝 → 联署失败，文件退回
                → 联署完成通知 → 仅推送到学团端
```

**关键代码位置：**
- 提交 `submit_document`：`backend/routers/delegate.py:126-133`（自动插入本代表团）
- 审批 `review_endorsement`：`backend/routers/delegate.py:244-330+`
- 联署完成推送：`backend/routers/delegate.py:323-340`
- 前端联署弹窗：`frontend/src/services/useWebSocket.js`

**关键实现细节（2026-09-04 修改）：**
```
非阁首提交 + need_endorsing=true → 自动 endorsing_list.insert(0, delegation_id)
→ 本代表团阁首在"联署审批"页面看到并审批
→ 任一拒绝 → endorsement_completed (result=rejected) → 学团端弹窗
```

### 5.2 代表团/代表数据

**测试账号（委员会7，密码全是 `123`）：**

| 代表团 | ID | 阁首 | 非阁首阁员 |
|--------|----|------|-----------|
| A团 | 25 | d5(205) | d1(200), d2(201) |
| B团 | 26 | d3(203) | d4(204) |
| C | 27 | C(206) | c2(209) |
| D | 28 | D(207) | d6(210) |
| E | 29 | E(208) | — |
| **F团** | **30** | **f1(211)** | **f2(212)** |
| **G团** | **31** | **g1(213)** | **g2(214)** |

学团端账号：`tstaff / tstaff123`

---

## 六、常见问题

### 6.1 部署后页面不更新
```
前端：清空 /var/www/munity/ 再解压（防止残留旧文件）
后端：systemctl restart mun-os.service（不要 pkill）
验证：curl https://munityos.cn 看 index.html 是否新版本
```

### 6.2 联署通知不显示
1. 确认 `review_endorsement` 代码被加载（`sed -n '320,340p' /root/mun-os/backend/routers/delegate.py` 看 `endorsement_completed`）
2. 确认前端有 `endorsement_completed` 监听：`grep -c 'endorsement_completed' /var/www/munity/assets/useWebSocket-*.js`（应返回 1）
3. 检查 journalctl 日志看 `[ENDORSEMENT_COMPLETED]` 是否出现
4. 检查测试时是否走的 HTTP API（直接 SQL 修改**不会**触发后端逻辑）

### 6.3 数据库文件丢失
```
# 重建方法：
1. 创建空文件：touch /root/mun-os/backend/mun_os.db
2. 从代码提取所有模型 CREATE TABLE 定义
3. 手动执行 SQL 重建表结构
4. 重建用户（学团账号、测试账号）
5. systemctl restart mun-os.service

# 包含的表：
delegations, users, staff_committees, documents, motions, agenda_items,
committee_timeline, messages, news, caucuses, states, directives, updates
```

### 6.4 后端报错无日志
```bash
# 检查 uvicorn 是否绑定正确端口
ss -tlnp | grep 8000

# 查看 systemd 日志
journalctl -u mun-os.service -n 50 --no-pager

# 如果日志为空的排查：
# 1. 确认服务正在运行（ps aux | grep uvicorn）
# 2. 检查是否有两个冲突的 uvicorn 进程（kill 旧进程）
# 3. 检查数据库文件是否存在
# 4. 检查 nginx 代理是否正常
```

### 6.5 MySQL JSON 字段突变陷阱
```python
# SQLAlchemy 不会检测 JSON 列的就地修改！
doc.endorsement_data[key] = value  # ← 这样不会触发 update
db.commit()                         # ← 这是 no-op！

# 正确做法：
from sqlalchemy.orm.attributes import flag_modified
doc.endorsement_data = modified_dict
flag_modified(doc, "endorsement_data")
db.commit()
```

---

## 七、Git 提交历史

当前最新的提交：
```
cf5c816 feat: 非阁首提交联署文件时自动加入本代表团，使阁首能审批打回
d844dc3 fix: 修复联署完成弹窗不显示 — WS异常级联跳过endorsement_completed推送
966facf feat: 联署完成时学团端弹窗提示（全屏模式除外）
...
```

**最新 commit `cf5c816` 包含的改动：**
- `backend/routers/delegate.py`：`submit_document` 添加非阁首代表自动插入本代表团逻辑（+6行）
- `backend/routers/delegate.py`：`review_endorsement` 添加 `print("[ENDORSEMENT_COMPLETED]...")` 调试日志（+2行）

---

## 八、⚠️ 当前已知问题

### 8.1 nginx 配置被覆盖（紧急）

**修复命令（待执行）：**
```bash
ssh root@47.116.65.0 "cp /etc/nginx/sites-available/munity.bak.20260909203533 \
   /etc/nginx/sites-available/munity \
   && nginx -t && systemctl reload nginx"
```

**后果**：如果不修复，`munityos.cn` 将：
- 只有 HTTP（无 HTTPS 加密）
- WebSocket 连接无法建立
- 前端指向 `/home/deploy/mun-os/frontend/dist/` 的旧构建

### 8.2 数据库无自动备份
- 建议添加定时任务：`cp /root/mun-os/backend/mun_os.db /root/mun-os/backend/backups/db.$(date +%Y%m%d).bak`

### 8.3 联署完成弹窗仍需用户侧验证
- 后端推送逻辑已修复并日志验证通过
- 前端 `endorsement_completed` 监听已部署
- 但用户上次报告"依旧没有通知"后暂停了排查，需要实际环境验证

---

## 九、快速启动

### 本地开发
```bash
cd /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/backend
source venv/bin/activate  # 如果有虚拟环境
uvicorn main:app --reload --port 8000

# 另一个终端
cd /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/frontend
npm run dev
```

### 线上部署（完整版）
```bash
cd /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/frontend
npm run build
tar czf /tmp/munity-frontend.tar.gz -C dist/ .
cat /tmp/munity-frontend.tar.gz | ssh root@47.116.65.0 "\
  rm -rf /var/www/munity/assets/* \
         /var/www/munity/favicon.svg \
         /var/www/munity/icons.svg \
         /var/www/munity/index.html \
  && tar xzf - -C /var/www/munity/"
scp /mnt/e/Chenyuewei/MUN/2026-08-30-munity-upgrade/backend/routers/*.py \
    root@47.116.65.0:/root/mun-os/backend/routers/
ssh root@47.116.65.0 "systemctl restart mun-os.service"
rm -f /tmp/munity-frontend.tar.gz
git add -A && git commit -m "..." && git push
```
