# MUNITY OS

模拟联合国会议管理系统 (Model United Nations Conference Management System)

## 功能特性

### 三级用户角色
- **管理员 (Admin)** - 管理学团账号、委员会配置
- **学团 (Staff)** - 会议控制、文件管理、投票表决
- **代表 (Delegate)** - 提交指令/文件、查看议程、接收更新

### 核心模块
- 📋 **议程管理** - 多层级议程设置与激活
- 📝 **点名系统** - 代表团出席记录
- 🎙️ **会议进行** - 动议管理、发言计时、发言名单
- 🗳️ **投票表决** - 绝对多数/简单多数/自定义规则
- 📄 **指令管理** - 代表提交指令，学团审核处理
- 📁 **文件管理** - 文件提交、发布、撤回
- 📢 **局势更新** - 学团发布更新，支持文件附件
- ⏱️ **时间线** - 会议时间模拟
- 💾 **存档/恢复** - 会议状态保存与恢复

### 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Element Plus + Pinia
- **认证**: JWT + bcrypt

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/YOUR_USERNAME/mun-os.git
cd mun-os
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
│   ├── models/          # 数据模型
│   ├── routers/         # API 路由
│   ├── services/        # 认证服务
│   ├── utils/           # 工具函数
│   ├── main.py          # 应用入口
│   ├── database.py      # 数据库配置
│   ├── config.py        # 系统配置
│   └── auto_save.py     # 自动保存
├── frontend/
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 公共组件
│   │   ├── stores/      # 状态管理
│   │   ├── router/      # 路由配置
│   │   └── api/         # API 封装
│   └── dist/            # 构建输出
└── README.md
```

## 部署

### 本地开发
```bash
# 后端 (热重载)
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端 (开发服务器)
cd frontend
npm run dev
```

### 生产部署
```bash
# 构建前端
cd frontend
npm run build

# 启动后端 (会自动服务前端静态文件)
cd ../backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker 部署 (可选)
```dockerfile
# TODO: 添加 Dockerfile
```

## 配置说明

### 环境变量
在 `backend/config.py` 中配置:
- `SECRET_KEY` - JWT 密钥
- `DATABASE_URL` - 数据库连接
- `DEFAULT_ADMIN_USERNAME` - 默认管理员用户名
- `DEFAULT_ADMIN_PASSWORD` - 默认管理员密码

### 委员会功能开关
管理员可以为每个委员会启用/禁用以下功能:
- 议程管理
- 指令管理
- 局势更新
- 时间线

## API 文档

启动服务后访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目链接: https://github.com/YOUR_USERNAME/mun-os
