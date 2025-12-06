from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# 用户相关模型
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


# 认证相关模型
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# 行程相关模型
class TripBase(BaseModel):
    title: str
    destination: str
    start_date: datetime
    end_date: datetime
    total_budget: float


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
    id: int
    user_id: int
    actual_expense: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 行程详情模型
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


# 费用记录模型
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


# AI行程生成请求模型
class TripGenerationRequest(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    budget: float
    travelers: int
    preferences: Dict[str, Any]


# 语音识别请求模型
class SpeechRecognitionRequest(BaseModel):
    audio_data: str  # base64编码的音频数据
    language: str = "zh-CN"


class SpeechRecognitionResponse(BaseModel):
    text: str
    confidence: float


# 地图服务请求模型
class MapSearchRequest(BaseModel):
    query: str
    location: Optional[Dict[str, float]] = None  # 经纬度
    radius: Optional[int] = 5000  # 搜索半径（米）


class MapDirectionsRequest(BaseModel):
    origin: Dict[str, float]  # 起点经纬度
    destination: Dict[str, float]  # 终点经纬度
    mode: str = "driving"  # driving/walking/transit