"""用户相关数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    username: str
    phone_number: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone_number: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    preferences: Dict[str, Any]
    
    class Config:
        from_attributes = True