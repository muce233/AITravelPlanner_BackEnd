from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_current_active_user
from ..schemas.map import MapSearchRequest, MapDirectionsRequest

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/search")
async def map_search(
    query: str,
    location: str = None,
    radius: int = 5000,
    current_user = Depends(get_current_active_user)
):
    """地点搜索（暂为占位实现）"""
    # TODO: 集成高德地图API
    return {
        "message": "地图搜索功能待实现",
        "query": query,
        "location": location,
        "radius": radius,
        "results": []
    }


@router.get("/directions")
async def map_directions(
    origin: str,
    destination: str,
    mode: str = "driving",
    current_user = Depends(get_current_active_user)
):
    """路线规划（暂为占位实现）"""
    # TODO: 集成高德地图API
    return {
        "message": "路线规划功能待实现",
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "route": None
    }


@router.get("/place/details")
async def place_details(
    place_id: str,
    current_user = Depends(get_current_active_user)
):
    """地点详情（暂为占位实现）"""
    # TODO: 集成高德地图API
    return {
        "message": "地点详情功能待实现",
        "place_id": place_id,
        "details": None
    }