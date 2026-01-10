from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip, TripDetail, User
from ..schemas.trip_detail import TripDetail as TripDetailSchema, TripDetailCreate, TripDetailUpdate

router = APIRouter(prefix="/api/trips/{trip_id}/details", tags=["trip_details"])


@router.post("/", response_model=TripDetailSchema)
async def create_trip_detail(
    trip_id: UUID,
    detail: TripDetailCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """添加行程详情"""
    # 检查行程是否存在且属于当前用户
    stmt = select(Trip).where(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
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
    await db.commit()
    await db.refresh(db_detail)
    return db_detail


@router.get("/", response_model=List[TripDetailSchema])
async def get_trip_details(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取行程详情列表"""
    # 检查行程是否存在且属于当前用户
    stmt = select(Trip).where(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    stmt = select(TripDetail).where(TripDetail.trip_id == trip_id)
    result = await db.execute(stmt)
    details = result.scalars().all()
    return details


@router.put("/{detail_id}", response_model=TripDetailSchema)
async def update_trip_detail(
    trip_id: UUID,
    detail_id: UUID,
    detail_update: TripDetailUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新行程详情"""
    # 检查行程是否存在且属于当前用户
    stmt = select(Trip).where(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 检查详情是否存在
    stmt = select(TripDetail).where(
        TripDetail.id == detail_id,
        TripDetail.trip_id == trip_id
    )
    result = await db.execute(stmt)
    detail = result.scalar_one_or_none()
    
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程详情不存在"
        )
    
    update_data = detail_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(detail, field, value)
    
    await db.commit()
    await db.refresh(detail)
    return detail


@router.delete("/{detail_id}")
async def delete_trip_detail(
    trip_id: UUID,
    detail_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除行程详情"""
    # 检查行程是否存在且属于当前用户
    stmt = select(Trip).where(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 检查详情是否存在
    stmt = select(TripDetail).where(
        TripDetail.id == detail_id,
        TripDetail.trip_id == trip_id
    )
    result = await db.execute(stmt)
    detail = result.scalar_one_or_none()
    
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程详情不存在"
        )
    
    await db.delete(detail)
    await db.commit()
    return {"message": "行程详情删除成功"}