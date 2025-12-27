# AI 旅行规划师 - 后端服务

基于 FastAPI 的现代化后端服务，为 AI 旅行规划师应用提供智能行程规划、费用跟踪、聊天对话和用户管理功能。本项目采用前后端分离架构，提供 RESTful API 和 WebSocket 实时通信支持，集成多个 AI 服务（OpenAI、DeepSeek、讯飞语音识别）和地图服务（高德地图），实现智能化的旅行规划体验。

## 🚀 功能特性

### 核心功能
- **用户认证与授权** - 基于 JWT 的安全认证系统，支持手机号登录和注册
- **智能行程规划** - AI 驱动的行程生成和优化，支持多目的地规划
- **行程管理** - 创建、查看、更新和删除旅行行程
- **行程详情管理** - 管理行程中的具体活动、景点、住宿等详细信息
- **费用管理** - 实时费用跟踪和预算分析，支持多种费用类型
- **智能对话** - 支持流式和非流式聊天补全，集成 DeepSeek AI
- **语音处理** - 基于 WebSocket 的实时语音识别，集成讯飞语音服务
- **地图集成** - 高德地图服务集成，提供地点搜索和路线规划
- **对话历史** - 完整的对话记录管理和消息历史查询

### 技术特性
- **API 限流** - 基于用户ID的请求频率限制，防止滥用
- **实时监控** - API调用日志和性能监控
- **CORS 支持** - 跨域资源共享配置，支持多前端域名
- **环境变量管理** - 灵活的配置管理，支持开发和生产环境
- **数据库迁移** - 自动创建数据库表结构
- **类型安全** - 使用 Pydantic 进行数据验证和类型检查
- **异步处理** - 基于 asyncio 的高性能异步请求处理

## 📋 环境要求

- Python 3.13.*
- uv（现代化 Python 包管理器）
- PostgreSQL 数据库（推荐）

## 🛠️ 技术栈

### 后端框架
- **FastAPI** - 现代化的 Python Web 框架，提供高性能的异步 API
- **SQLAlchemy** - Python SQL 工具包和对象关系映射（ORM）
- **Pydantic** - 数据验证和设置管理，使用 Python 类型注解

### 数据库
- **PostgreSQL** - 关系型数据库管理系统
- **psycopg2** - PostgreSQL 数据库适配器

### 认证与安全
- **python-jose** - JWT 令牌的创建和验证
- **passlib** - 密码哈希和验证
- **python-multipart** - 支持表单数据解析

### AI 服务集成
- **OpenAI** - AI 模型接口（用于行程规划）
- **DeepSeek** - 聊天对话 AI 服务
- **讯飞语音识别** - 语音转文字服务

### 地图服务
- **高德地图 API** - 地点搜索、路线规划等地图服务

### 开发工具
- **uvicorn** - ASGI 服务器
- **black** - Python 代码格式化工具
- **flake8** - Python 代码检查工具
- **mypy** - Python 静态类型检查工具

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

### 主要 API 端点

#### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新访问令牌

#### 用户管理
- `GET /api/users/me` - 获取当前用户信息
- `PUT /api/users/me` - 更新当前用户信息

#### 行程管理
- `GET /api/trips` - 获取用户的所有行程
- `POST /api/trips` - 创建新行程
- `GET /api/trips/{trip_id}` - 获取指定行程详情
- `PUT /api/trips/{trip_id}` - 更新行程信息
- `DELETE /api/trips/{trip_id}` - 删除行程

#### 行程详情
- `GET /api/trip-details/{trip_id}` - 获取行程的所有详情
- `POST /api/trip-details` - 创建行程详情
- `PUT /api/trip-details/{detail_id}` - 更新行程详情
- `DELETE /api/trip-details/{detail_id}` - 删除行程详情

#### 费用管理
- `GET /api/expenses` - 获取费用记录
- `POST /api/expenses` - 创建费用记录
- `PUT /api/expenses/{expense_id}` - 更新费用记录
- `DELETE /api/expenses/{expense_id}` - 删除费用记录
- `GET /api/expenses/summary/{trip_id}` - 获取行程费用汇总

#### 智能对话
- `POST /api/chat/completions` - 非流式对话补全
- `POST /api/chat/completions/stream` - 流式对话补全
- `GET /api/conversations` - 获取对话历史
- `GET /api/conversations/{conversation_id}` - 获取指定对话
- `DELETE /api/conversations/{conversation_id}` - 删除对话

#### 语音识别
- `WS /api/speech/recognize` - WebSocket 实时语音识别

#### 地图服务
- `GET /api/map/search` - 地点搜索
- `GET /apiMap/route` - 路线规划

## 🔑 测试账号

为了方便测试，系统提供了默认测试账号：
- **用户名/手机号**: `15666666666`
- **密码**: `666666`

## 📁 项目结构

```
AITravelPlanner_BackEnd/
├── app/
│   ├── __init__.py
│   ├── auth.py                 # 认证逻辑（JWT令牌生成和验证、密码哈希）
│   ├── config.py               # 配置管理（数据库连接、环境变量加载）
│   ├── database.py             # 数据库连接（SQLAlchemy引擎和会话管理）
│   ├── middleware/
│   │   └── rate_limit.py       # 限流中间件（基于用户ID的请求频率限制）
│   ├── models/                 # SQLAlchemy 数据模型（数据库表定义）
│   │   ├── user.py             # 用户模型（用户信息、密码哈希）
│   │   ├── trip.py             # 行程模型（行程基本信息）
│   │   ├── trip_detail.py      # 行程详情模型（行程中的活动、景点）
│   │   ├── expense.py          # 费用模型（费用记录、类型、金额）
│   │   └── conversation.py     # 对话模型（对话记录、消息关联）
│   ├── routers/                # API 路由处理器（端点定义）
│   │   ├── auth.py             # 认证路由（登录、注册、令牌刷新）
│   │   ├── users.py            # 用户管理路由（用户信息查询和更新）
│   │   ├── trips.py            # 行程管理路由（CRUD操作）
│   │   ├── trip_details.py     # 行程详情路由（详情管理）
│   │   ├── expenses.py         # 费用管理路由（费用记录管理）
│   │   ├── chat.py             # 聊天对话路由（流式和非流式对话）
│   │   ├── speech.py           # 语音处理路由（WebSocket语音识别）
│   │   └── map.py              # 地图服务路由（地点搜索、路线规划）
│   ├── schemas/                # Pydantic 数据模式（请求/响应模型）
│   │   ├── auth.py             # 认证模式（登录、注册请求/响应）
│   │   ├── user.py             # 用户模式（用户信息模型）
│   │   ├── trip.py             # 行程模式（行程数据模型）
│   │   ├── trip_detail.py      # 行程详情模式（详情数据模型）
│   │   ├── expense.py          # 费用模式（费用数据模型）
│   │   ├── chat.py             # 聊天模式（对话请求/响应）
│   │   ├── speech.py           # 语音模式（语音识别请求/响应）
│   │   ├── map.py              # 地图模式（地图服务请求/响应）
│   │   └── ai.py               # AI服务模式（AI请求/响应）
│   └── services/               # 业务逻辑服务（核心业务逻辑）
│       ├── chat_client.py      # 聊天客户端（DeepSeek API集成）
│       └── conversation_service.py # 对话服务（对话历史管理）
├── docs/                       # 文档目录
├── tests/                      # 测试文件（单元测试和集成测试）
├── main.py                     # FastAPI 应用入口（应用初始化、路由注册）
├── run.py                      # 应用启动脚本（开发环境启动）
├── pyproject.toml              # 项目配置（依赖管理、工具配置）
├── .env.example                # 环境变量示例文件
└── README.md                   # 说明文档
```

### 核心模块说明

#### 认证模块 (app/auth.py)
- JWT 令牌生成和验证
- 密码哈希和验证
- 用户身份认证

#### 数据库模块 (app/database.py)
- SQLAlchemy 引擎配置
- 数据库会话管理
- 自动创建数据库表

#### 中间件 (app/middleware/rate_limit.py)
- 基于用户ID的请求频率限制
- 防止 API 滥用
- 可配置的限流策略

#### 路由模块 (app/routers/)
- **auth.py**: 用户登录、注册、令牌刷新
- **users.py**: 用户信息查询和更新
- **trips.py**: 行程的创建、查询、更新、删除
- **trip_details.py**: 行程详情的管理
- **expenses.py**: 费用记录的增删改查
- **chat.py**: 智能对话，支持流式和非流式响应
- **speech.py**: WebSocket 实时语音识别
- **map.py**: 地图服务，包括地点搜索和路线规划

#### 服务模块 (app/services/)
- **chat_client.py**: DeepSeek API 客户端，处理 AI 对话请求
- **conversation_service.py**: 对话历史管理，消息存储和检索

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