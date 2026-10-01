# MUNITY OS

模拟联合国会议管理系统 (Model United Nations Conference Management System)

## 功能特性

### 三级用户角色
- **管理员 (Admin)** - 管理学团账号、委员会配置
- **学团 (Staff)** - 会议控制、文件管理、投票表决、非对称消息管理
- **代表 (Delegate)** - 提交指令/文件、查看议程、接收更新、非对称消息收发

### 核心模块
- 📋 **议程管理** - 多层级议程设置与激活
- 📝 **点名系统** - 代表团出席记录
- 🎙️ **会议进行** - 动议管理、发言计时、发言名单
- 🗳️ **投票表决** - 绝对多数/简单多数/自定义规则
- 📄 **指令管理** - 代表提交指令，学团审核处理
- 📁 **文件管理** - 文件提交、发布、撤回、联署
- 📢 **局势更新** - 学团发布更新，支持文件附件
- 🕊️ **非对称消息** - 危机联动核心功能，支持公开/代表团/私密三级消息
- 🔔 **WebSocket 实时推送** - 新消息即时通知，无需手动刷新
- 📈 **服务器资源监控** - CPU/内存/磁盘历史曲线 + 每 2 秒实时推送
- ⏱️ **时间线** - 会议时间模拟
- 💾 **存档/恢复** - 会议状态保存与恢复

### 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Element Plus + Pinia
- **认证**: JWT + bcrypt
- **实时通信**: WebSocket

### 数据关系
删除委员会会级联清除其下全部关联数据：代表团、代表、议程、动议、发言名单、点名、
指令、文件、局势更新、发言记录、时间线、投票及投票记录、非对称消息、学团-委员会关联。
学团账号本身保留，仅解除与委员会的关联（学团可复用）。

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/cyw0715/MUNITY.git
cd MUNITY
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd ../frontend
npm install
```

4. 构建前端
```bash
npm run build
```

5. 启动服务
```bash
cd ../backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

6. 访问系统
打开浏览器访问 `http://localhost:8000`

### 默认账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 通过环境变量 DEFAULT_ADMIN_PASSWORD 设置（未设置时启动日志打印一次性随机密码） |
| 学团 | 由管理员创建 | 创建时设定 |

### 环境变量（生产环境必读）

| 变量 | 说明 | 默认 |
|------|------|------|
| `SECRET_KEY` | JWT 签名密钥。**生产环境必须设置**，否则启动即退出 | 开发环境随机生成（重启后旧 token 失效） |
| `DEFAULT_ADMIN_PASSWORD` | 首次启动创建的管理员口令，至少 8 位且不得为常见弱口令 | 随机生成并打印到日志 |
| `ENV` | 设为 `production` 时启用生产校验（要求 SECRET_KEY、收紧 CORS） | 空 |
| `CORS_ORIGINS` | 允许的跨域来源，逗号分隔 | 开发环境放行 localhost |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | 单 IP 每分钟登录尝试上限 | 5 |
| `LOGIN_LOCKOUT_SECONDS` | 超限后的锁定时长（秒） | 300 |
| `MAX_UPLOAD_BYTES` | 上传文件大小上限 | 20MB |

建议放在 `/etc/munity/munity.env`，由 systemd 的 `EnvironmentFile` 注入（见 `deploy/munity.service`）。

## 项目结构

```
mun-os/
├── backend/
│   ├── models/          # 数据模型（含非对称消息）
│   ├── routers/         # API 路由（含非对称消息 + WebSocket）
│   ├── services/        # 认证服务 + WebSocket 管理器
│   ├── utils/           # 工具函数（路径清洗、上传校验、登录限流）
│   ├── main.py          # 应用入口（含实时监控推送任务）
│   ├── monitor.py       # 服务器资源采集（历史归档 + 实时采样）
│   ├── database.py      # 数据库配置
│   ├── config.py        # 系统配置
│   └── auto_save.py     # 自动保存
├── frontend/
│   ├── src/
│   │   ├── views/       # 页面组件（含非对称消息页面）
│   │   ├── components/  # 公共组件
│   │   ├── stores/      # 状态管理
│   │   ├── router/      # 路由配置
│   │   ├── composables/ # 组合式函数（含 WebSocket 连接管理）
│   │   └── api/         # API 封装
│   └── dist/            # 构建输出
├── deploy/              # 部署配置
├── LICENSE              # PolyForm Shield License 1.0.0
└── README.md
```

## 非对称消息系统

非对称消息是危机联动模拟的核心功能，支持三种可见性级别：

| 可见性 | 说明 |
|--------|------|
| **公开 (public)** | 委员会内所有代表可见 |
| **代表团 (delegation)** | 仅指定代表团的成员可见 |
| **私密 (private)** | 仅指定代表可见 |

学团可发布、撤回非对称消息。代表收到消息后会通过 WebSocket 实时推送通知，无需手动刷新页面。

## API 文档

启动服务后访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- WebSocket: `ws://localhost:8000/api/ws/{user_id}`

## 部署

`deploy/` 目录提供了一键部署脚本与配置：

- `deploy/deploy.sh` — 安装依赖、构建前端、配置 Nginx 与 systemd
- `deploy/munity.service` — systemd 单元（含 `ProtectSystem` 等沙箱加固）
- `deploy/nginx.conf` — Nginx 站点配置模板

### Nginx 必须转发 WebSocket 升级头

反代 `/api/` 时若缺少以下配置，`/api/ws/*` 会退化成普通 HTTP 请求并返回 404，
导致**所有实时功能静默失效**（消息通知、会议同步、资源实时监控）：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;   # 需在 http{} 定义 map
    proxy_read_timeout 3600s;                          # 避免空闲长连接被切断
}
```

其中 `map` 需定义在 `http` 上下文（可放在 `/etc/nginx/conf.d/websocket_upgrade.conf`）：

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

PolyForm Shield License 1.0.0 — 详见 [LICENSE](./LICENSE)

本许可证允许个人、学习、研究等非竞争性使用。不得使用本软件提供与本项目竞争的产品或服务。具体条款见许可证全文。

## 联系方式

- 项目链接: https://github.com/cyw0715/MUNITY
