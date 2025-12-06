# AI 旅行规划师 - 后端服务

基于 FastAPI 的现代化后端服务，为 AI 旅行规划师应用提供智能行程规划、费用跟踪、聊天对话和用户管理功能。

## 🚀 功能特性

- **用户认证与授权** - 基于 JWT 的安全认证系统
- **智能行程规划** - AI 驱动的行程生成和优化
- **费用管理** - 实时费用跟踪和预算分析
- **智能对话** - 支持流式和非流式聊天补全
- **语音处理** - 语音识别和语音命令支持
- **地图集成** - 高德地图服务集成
- **API 限流** - 基于用户ID的请求频率限制
- **实时监控** - API调用日志和性能监控

## 📋 环境要求

- Python 3.13.*
- uv（现代化 Python 包管理器）
- PostgreSQL 数据库（推荐）

## 🛠️ 安装指南

### 1. 克隆仓库
```bash
git clone <仓库地址>
cd AITravelPlanner_BackEnd
```

### 2. 安装依赖
```bash
# 安装生产环境依赖
uv sync

# 安装开发环境依赖
uv sync --dev
```

### 3. 环境配置

复制 `.env.example` 文件为 `.env` 并配置：
```env
# 数据库配置
DATABASE_URL=postgresql://用户名:密码@localhost:5432/travel_planner
SECRET_KEY=你的密钥
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI服务配置
OPENAI_API_KEY=你的-openai-api密钥
AI_SERVICE_URL=https://api.openai.com/v1

# 聊天API配置
CHAT_API_KEY=你的-deepseek-api密钥
CHAT_API_URL=https://api.deepseek.com/v1

# 语音识别服务配置
SPEECH_RECOGNITION_API_KEY=你的-讯飞-api密钥
SPEECH_SERVICE_URL=https://api.xfyun.cn/v1

# 地图服务配置
AMAP_API_KEY=你的-高德地图-api密钥

# 应用配置
DEBUG=true
APP_NAME=AI Travel Planner API

# CORS配置
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173
```

## 🏃‍♂️ 运行应用

### 开发模式
```bash
uv run python main.py
```
服务器将启动在 `http://localhost:8000`

### 使用 run.py 启动
```bash
uv run python run.py
```

## 📚 API 文档

服务器启动后，可以访问以下文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI 架构**: `http://localhost:8000/openapi.json`

## 🔑 测试账号

为了方便测试，系统提供了默认测试账号：
- **用户名/手机号**: `15666666666`
- **密码**: `666666`

## 📁 项目结构

```
AITravelPlanner_BackEnd/
├── app/
│   ├── __init__.py
│   ├── auth.py                 # 认证逻辑
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── middleware/
│   │   └── rate_limit.py       # 限流中间件
│   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── trip.py             # 行程模型
│   │   ├── trip_detail.py      # 行程详情模型
│   │   ├── expense.py          # 费用模型
│   │   └── conversation.py     # 对话模型
│   ├── routers/                # API 路由处理器
│   │   ├── auth.py             # 认证路由
│   │   ├── users.py            # 用户管理路由
│   │   ├── trips.py            # 行程管理路由
│   │   ├── trip_details.py     # 行程详情路由
│   │   ├── expenses.py         # 费用管理路由
│   │   ├── chat.py             # 聊天对话路由
│   │   ├── speech.py           # 语音处理路由
│   │   └── map.py              # 地图服务路由
│   ├── schemas/                # Pydantic 数据模式
│   │   ├── auth.py             # 认证模式
│   │   ├── user.py             # 用户模式
│   │   ├── trip.py             # 行程模式
│   │   ├── trip_detail.py      # 行程详情模式
│   │   ├── expense.py          # 费用模式
│   │   ├── chat.py             # 聊天模式
│   │   ├── speech.py           # 语音模式
│   │   ├── map.py              # 地图模式
│   │   └── ai.py               # AI服务模式
│   └── services/               # 业务逻辑服务
│       ├── chat_client.py      # 聊天客户端
│       └── conversation_service.py # 对话服务
├── docs/                       # 文档目录
├── tests/                      # 测试文件
├── main.py                     # FastAPI 应用入口
├── run.py                      # 应用启动脚本
├── pyproject.toml              # 项目配置
└── README.md                   # 说明文档
```

## 🔐 认证机制

API 使用 JWT（JSON Web Tokens）进行认证。在请求头中包含令牌：

```http
Authorization: Bearer <你的-jwt-令牌>
```

### 获取访问令牌
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "15666666666", "password": "666666"}'
```

## 📊 数据库

### 数据库表结构
主要数据表包括：
- `users` - 用户账户和资料
- `trips` - 行程信息和行程安排
- `trip_details` - 行程详情和活动安排
- `expenses` - 费用记录
- `conversations` - 对话记录
- `messages` - 消息记录

### 自动创建表
应用启动时会自动创建所有必要的数据库表。

## � 开发命令

### 代码格式化
```bash
uv run black .
```

### 代码检查
```bash
uv run flake8
```

### 类型检查
```bash
uv run mypy .
```

## 🚢 部署

### 手动部署
1. 设置生产环境变量
2. 安装依赖：`uv sync`
3. 运行：`uv run python main.py`

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/新功能`
3. 提交更改：`git commit -m '添加新功能'`
4. 推送到分支：`git push origin feature/新功能`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🆘 技术支持

如果遇到问题：

1. 查看 [API 文档](http://localhost:8000/docs)
2. 检查日志中的错误信息
3. 在仓库中创建 Issue

## 🔄 更新日志

### v0.1.0 (当前版本)
- 初始版本发布
- 基础用户认证系统
- 行程管理功能
- 费用跟踪功能
- 智能对话功能
- 语音处理支持
- 地图服务集成

## 🎯 开发路线图

- [ ] 集成更多地图服务提供商
- [ ] 添加实时协作功能
- [ ] 实现离线模式支持
- [ ] 优化 AI 行程规划算法
- [ ] 增加移动端优化 API