"""行程详情数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class TripDetailBase(BaseModel):
    day: int
    type: str  # 景点/住宿/餐厅/交通
    name: str
    location: Optional[Dict[str, float]] = None  # 经纬度
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    price: float = 0.0
    notes: Optional[str] = None
    images: Optional[List[str]] = None


class TripDetailCreate(TripDetailBase):
    pass


class TripDetailUpdate(BaseModel):
    day: Optional[int] = None
    type: Optional[str] = None
    name: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    price: Optional[float] = None
    notes: Optional[str] = None
    images: Optional[List[str]] = None


class TripDetail(TripDetailBase):
    id: int
    trip_id: int
    
    class Config:
        from_attributes = True