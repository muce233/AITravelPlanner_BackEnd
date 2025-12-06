from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip, TripDetail, User
from ..schemas.trip_detail import TripDetail, TripDetailCreate, TripDetailUpdate

router = APIRouter(prefix="/api/trips/{trip_id}/details", tags=["trip_details"])


@router.post("/", response_model=TripDetail)
def create_trip_detail(
    trip_id: int,
    detail: TripDetailCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """添加行程详情"""
    # 检查行程是否存在且属于当前用户
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    db_detail = TripDetail(
        trip_id=trip_id,
        day=detail.day,
        type=detail.type,
        name=detail.name,
        location=detail.location,
        address=detail.address,
        start_time=detail.start_time,
        end_time=detail.end_time,
        description=detail.description,
        price=detail.price,
        notes=detail.notes,
        images=detail.images
    )
    
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail


@router.get("/", response_model=List[TripDetail])
def get_trip_details(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取行程详情列表"""
    # 检查行程是否存在且属于当前用户
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    details = db.query(TripDetail).filter(TripDetail.trip_id == trip_id).all()
    return details


@router.put("/{detail_id}", response_model=TripDetail)
def update_trip_detail(
    trip_id: int,
    detail_id: int,
    detail_update: TripDetailUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新行程详情"""
    # 检查行程是否存在且属于当前用户
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 检查详情是否存在
    detail = db.query(TripDetail).filter(
        TripDetail.id == detail_id,
        TripDetail.trip_id == trip_id
    ).first()
    
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程详情不存在"
        )
    
    update_data = detail_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(detail, field, value)
    
    db.commit()
    db.refresh(detail)
    return detail


@router.delete("/{detail_id}")
def delete_trip_detail(
    trip_id: int,
    detail_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除行程详情"""
    # 检查行程是否存在且属于当前用户
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 检查详情是否存在
    detail = db.query(TripDetail).filter(
        TripDetail.id == detail_id,
        TripDetail.trip_id == trip_id
    ).first()
    
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程详情不存在"
        )
    
    db.delete(detail)
    db.commit()
    return {"message": "行程详情删除成功"}