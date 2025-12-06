"""行程详情相关数据库模型"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


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