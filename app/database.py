from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False  # 添加这一行，防止提交后对象属性过期
)

# 创建基类
Base = declarative_base()


async def get_db():
    """异步数据库依赖注入"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """异步创建数据库表"""
    # 导入所有模型以确保它们被注册到Base.metadata中
    from .models import User, Trip, TripDetail, Expense, Conversation, ConversationMessage, APILog
    
    # 异步创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)