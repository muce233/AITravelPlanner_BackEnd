from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip, User
from ..schemas.trip import Trip, TripCreate, TripUpdate

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("/", response_model=Trip)
def create_trip(
    trip: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新行程"""
    db_trip = Trip(
        user_id=current_user.id,
        title=trip.title,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        total_budget=trip.total_budget
    )
    
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


@router.get("/", response_model=List[Trip])
def get_user_trips(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户所有行程"""
    trips = db.query(Trip).filter(Trip.user_id == current_user.id).all()
    return trips


@router.get("/{trip_id}", response_model=Trip)
def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定行程详情"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    return trip


@router.put("/{trip_id}", response_model=Trip)
def update_trip(
    trip_id: int,
    trip_update: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新行程信息"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    update_data = trip_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    
    db.commit()
    db.refresh(trip)
    return trip


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除行程"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    db.delete(trip)
    db.commit()
    return {"message": "行程删除成功"}


@router.post("/{trip_id}/generate")
def generate_ai_trip(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成AI行程（暂为占位实现）"""
    # 检查行程是否存在
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # TODO: 集成AI服务生成详细行程
    return {"message": "AI行程生成功能待实现", "trip_id": trip_id}