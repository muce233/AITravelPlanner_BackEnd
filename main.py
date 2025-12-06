from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.routers import users, auth, trips, trip_details, expenses, speech, map, chat
from app.middleware.rate_limit import setup_rate_limit_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    create_tables()
    print("数据库表创建完成")
    yield
    # 关闭时清理资源
    print("应用正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="AI旅行规划师后端API",
    version="0.1.0",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置限流中间件
setup_rate_limit_middleware(app)

# 注册路由
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(trip_details.router)
app.include_router(expenses.router)
app.include_router(speech.router)
app.include_router(map.router)
app.include_router(chat.router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "AI旅行规划师后端API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )