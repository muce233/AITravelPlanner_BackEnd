"""地图服务相关数据模型"""
from pydantic import BaseModel
from typing import Optional, Dict


class MapSearchRequest(BaseModel):
    query: str
    location: Optional[Dict[str, float]] = None  # 经纬度
    radius: Optional[int] = 5000  # 搜索半径（米）


class MapDirectionsRequest(BaseModel):
    origin: Dict[str, float]  # 起点经纬度
    destination: Dict[str, float]  # 终点经纬度
    mode: str = "driving"  # driving/walking/transit