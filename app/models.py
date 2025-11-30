from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    preferences = Column(JSON, default={})


class Trip(Base):
    """行程表"""
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    destination = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_budget = Column(Float, default=0.0)
    actual_expense = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TripDetail(Base):
    """行程详情表"""
    __tablename__ = "trip_details"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    day = Column(Integer, nullable=False)  # 第几天
    type = Column(String(50), nullable=False)  # 景点/住宿/餐厅/交通
    name = Column(String(200), nullable=False)
    location = Column(JSON)  # 位置（经纬度）
    address = Column(String(500))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    description = Column(Text)
    price = Column(Float, default=0.0)
    notes = Column(Text)
    images = Column(JSON)  # 图片链接（JSON数组）


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