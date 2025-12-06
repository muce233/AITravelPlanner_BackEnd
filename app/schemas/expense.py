"""费用记录数据模型"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExpenseBase(BaseModel):
    category: str  # 餐饮/交通/住宿/购物/其他
    amount: float
    currency: str = "CNY"
    date: datetime
    description: Optional[str] = None
    receipt_image: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    receipt_image: Optional[str] = None


class Expense(ExpenseBase):
    id: int
    trip_id: int
    
    class Config:
        from_attributes = True