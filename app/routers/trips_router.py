from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip as TripModel, User, Conversation
from ..schemas.trip import Trip, TripCreate, TripUpdate
from ..services.conversation_service import ConversationService
from ..schemas.chat import CreateConversationRequest

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("/quick", response_model=Trip)
async def create_quick_trip(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """快速创建空行程，无需传入任何参数，同时创建关联的对话会话"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    db_trip = TripModel(
        user_id=current_user.id,
        title="新行程",
        destination="",
        start_date=today,
        end_date=tomorrow,
        total_budget=0.0
    )
    
    db.add(db_trip)
    await db.commit()
    await db.refresh(db_trip)
    
    # 创建关联的对话会话
    conversation_service = ConversationService(db)
    conversation_request = CreateConversationRequest(title=db_trip.title)
    conversation = await conversation_service.create_conversation(
        user_id=current_user.id,
        request=conversation_request,
        trip_id=db_trip.id
    )
    
    # 创建Trip schema对象并添加conversation_id
    trip_dict = {
        "id": db_trip.id,
        "user_id": db_trip.user_id,
        "title": db_trip.title,
        "destination": db_trip.destination,
        "start_date": db_trip.start_date,
        "end_date": db_trip.end_date,
        "total_budget": db_trip.total_budget,
        "actual_expense": db_trip.actual_expense,
        "conversation_id": conversation.id,
        "created_at": db_trip.created_at,
        "updated_at": db_trip.updated_at
    }
    
    return Trip(**trip_dict)


@router.post("", response_model=Trip)
async def create_trip(
    trip: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新行程，支持创建空行程，同时创建关联的对话会话"""
    db_trip = TripModel(
        user_id=current_user.id,
        title=trip.title,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        total_budget=trip.total_budget if trip.total_budget is not None else 0.0
    )
    
    db.add(db_trip)
    await db.commit()
    await db.refresh(db_trip)
    
    # 创建关联的对话会话
    conversation_service = ConversationService(db)
    conversation_request = CreateConversationRequest(title=db_trip.title)
    conversation = await conversation_service.create_conversation(
        user_id=current_user.id,
        request=conversation_request,
        trip_id=db_trip.id
    )
    
    # 创建Trip schema对象并添加conversation_id
    trip_dict = {
        "id": db_trip.id,
        "user_id": db_trip.user_id,
        "title": db_trip.title,
        "destination": db_trip.destination,
        "start_date": db_trip.start_date,
        "end_date": db_trip.end_date,
        "total_budget": db_trip.total_budget,
        "actual_expense": db_trip.actual_expense,
        "conversation_id": conversation.id,
        "created_at": db_trip.created_at,
        "updated_at": db_trip.updated_at
    }
    
    return Trip(**trip_dict)


@router.get("", response_model=List[Trip])
async def get_user_trips(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户所有行程，同时获取关联的conversation_id"""
    from sqlalchemy.orm import selectinload
    
    # 使用left join关联Conversation表，获取每个trip对应的conversation_id
    stmt = (
        select(TripModel)
        .outerjoin(Conversation, TripModel.id == Conversation.trip_id)
        .where(TripModel.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    trips = result.scalars().all()
    
    # 为每个trip添加conversation_id
    trip_list = []
    for trip in trips:
        # 查询关联的conversation
        conv_stmt = select(Conversation.id).where(Conversation.trip_id == trip.id)
        conv_result = await db.execute(conv_stmt)
        conversation_id = conv_result.scalar_one_or_none()
        
        # 如果没有关联的conversation，跳过该行程
        if not conversation_id:
            continue
        
        # 创建Trip schema对象并添加conversation_id
        trip_dict = {
            "id": trip.id,
            "user_id": trip.user_id,
            "title": trip.title,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "total_budget": trip.total_budget,
            "actual_expense": trip.actual_expense,
            "conversation_id": conversation_id,
            "created_at": trip.created_at,
            "updated_at": trip.updated_at
        }
        trip_list.append(Trip(**trip_dict))
    
    return trip_list


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取特定行程详情，同时获取关联的conversation_id"""
    stmt = select(TripModel).where(
        TripModel.id == trip_id,
        TripModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # 查询关联的conversation
    conv_stmt = select(Conversation.id).where(Conversation.trip_id == trip.id)
    conv_result = await db.execute(conv_stmt)
    conversation_id = conv_result.scalar_one_or_none()
    
    # 如果没有关联的conversation，返回404错误
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程关联的对话不存在"
        )
    
    # 创建Trip schema对象并添加conversation_id
    trip_dict = {
        "id": trip.id,
        "user_id": trip.user_id,
        "title": trip.title,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "total_budget": trip.total_budget,
        "actual_expense": trip.actual_expense,
        "conversation_id": conversation_id,
        "created_at": trip.created_at,
        "updated_at": trip.updated_at
    }
    
    return Trip(**trip_dict)


@router.put("/{trip_id}", response_model=Trip)
async def update_trip(
    trip_id: UUID,
    trip_update: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新行程信息"""
    stmt = select(TripModel).where(
        TripModel.id == trip_id,
        TripModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    update_data = trip_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    
    await db.commit()
    await db.refresh(trip)
    
    # 查询关联的conversation
    conv_stmt = select(Conversation.id).where(Conversation.trip_id == trip.id)
    conv_result = await db.execute(conv_stmt)
    conversation_id = conv_result.scalar_one_or_none()
    
    # 如果没有关联的conversation，返回404错误
    if not conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程关联的对话不存在"
        )
    
    # 创建Trip schema对象并添加conversation_id
    trip_dict = {
        "id": trip.id,
        "user_id": trip.user_id,
        "title": trip.title,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "total_budget": trip.total_budget,
        "actual_expense": trip.actual_expense,
        "conversation_id": conversation_id,
        "created_at": trip.created_at,
        "updated_at": trip.updated_at
    }
    
    return Trip(**trip_dict)


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除行程"""
    stmt = select(TripModel).where(
        TripModel.id == trip_id,
        TripModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    await db.delete(trip)
    await db.commit()
    return {"message": "行程删除成功"}


@router.post("/{trip_id}/generate")
async def generate_ai_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成AI行程（暂为占位实现）"""
    # 检查行程是否存在
    stmt = select(TripModel).where(
        TripModel.id == trip_id,
        TripModel.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在"
        )
    
    # TODO: 集成AI服务生成详细行程
    return {"message": "AI行程生成功能待实现", "trip_id": trip_id}