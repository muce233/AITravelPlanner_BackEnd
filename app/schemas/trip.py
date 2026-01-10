"""行程相关数据模型"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class TripBase(BaseModel):
    title: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = None
    actual_expense: Optional[float] = None


class Trip(TripBase):
    id: UUID
    user_id: int
    actual_expense: float
    conversation_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True