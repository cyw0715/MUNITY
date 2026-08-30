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
- 📁 **文件管理** - 文件提交、发布、撤回
- 📢 **局势更新** - 学团发布更新，支持文件附件
- 🕊️ **非对称消息** - 危机联动核心功能，支持公开/代表团/私密三级消息
- 🔔 **WebSocket 实时推送** - 新消息即时通知，无需手动刷新
- ⏱️ **时间线** - 会议时间模拟
- 💾 **存档/恢复** - 会议状态保存与恢复

### 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Element Plus + Pinia
- **认证**: JWT + bcrypt
- **实时通信**: WebSocket

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
| 管理员 | admin | admin123 |
| 学团 | cyw | 123456 |

## 项目结构

```
mun-os/
├── backend/
│   ├── models/          # 数据模型（含非对称消息）
│   ├── routers/         # API 路由（含非对称消息 + WebSocket）
│   ├── services/        # 认证服务 + WebSocket 管理器
│   ├── utils/           # 工具函数
│   ├── main.py          # 应用入口
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
