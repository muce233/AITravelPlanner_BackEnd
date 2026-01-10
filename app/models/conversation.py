"""对话会话相关数据库模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from ..database import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), nullable=True)  # 关联行程ID，一个trips一个conversations，使用uuid类型，无外键约束
    model = Column(String(50), nullable=False, default="chat-model")
    messages = Column(JSON, default=[])  # 存储消息历史
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConversationMessage(Base):
    """对话消息表（可选，用于更详细的消息管理）"""
    __tablename__ = "conversation_messages"
    
    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    name = Column(String(100))  # 消息发送者名称
    tokens = Column(Integer, default=0)  # token数量
    tool_json = Column(JSON)  # 工具调用JSON数据
    message_type = Column(String(50), default="normal")  # 消息类型: normal, tool_call_status, tool_result
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class APILog(Base):
    """API调用日志表"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(100), nullable=False)
    model = Column(String(50))
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Integer, default=0)  # 成本（单位：分）
    response_time = Column(Integer)  # 响应时间（毫秒）
    status_code = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())