"""费用相关数据库模型"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class Expense(Base):
    """费用记录表"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    category = Column(String(50), nullable=False)  # 餐饮/交通/住宿/购物/其他
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    date = Column(DateTime, nullable=False)
    description = Column(String(500))
    receipt_image = Column(String(500))  # 凭证图片路径