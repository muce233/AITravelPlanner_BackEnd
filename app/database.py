from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """数据库依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建数据库表"""
    # 导入所有模型以确保它们被注册到Base.metadata中
    from .models import User, Trip, TripDetail, Expense, Conversation, ConversationMessage, APILog
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)