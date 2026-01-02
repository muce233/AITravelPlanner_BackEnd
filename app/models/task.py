"""任务相关数据库模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base


class AITask(Base):
    """AI任务表"""
    __tablename__ = "ai_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    task_type = Column(String(50), nullable=False, index=True, comment="任务类型")
    title = Column(String(200), nullable=False, comment="任务标题")
    details = Column(Text, nullable=False, comment="任务详细描述")
    sort_num = Column(Integer, nullable=False, default=1, comment="排序号")
    status = Column(String(20), nullable=False, default="未开始", comment="任务状态")
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, comment="对话ID")
    conversation_messages_id = Column(Integer, ForeignKey("conversation_messages.id"), nullable=True, comment="对话消息ID")
    result = Column(JSON, default=None, comment="任务执行结果")
    error = Column(Text, default=None, comment="错误信息")
    function_calls = Column(JSON, default=None, comment="调用的Function列表")
    execution_time = Column(Integer, default=None, comment="执行时间(毫秒)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    completed_at = Column(DateTime(timezone=True), default=None, comment="完成时间")
