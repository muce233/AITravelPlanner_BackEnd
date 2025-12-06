"""AI相关数据模型"""
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class TripGenerationRequest(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    budget: float
    travelers: int
    preferences: Dict[str, Any]