from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip, Expense, User
from ..schemas.expense import Expense, ExpenseCreate, ExpenseUpdate

router = APIRouter(prefix="/api/trips/{trip_id}/expenses", tags=["expenses"])


@router.post("/", response_model=Expense)
async def create_expense(
    trip_id: int,
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """添加费用记录"""
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
    
    db_expense = Expense(
        trip_id=trip_id,
        category=expense.category,
        amount=expense.amount,
        currency=expense.currency,
        date=expense.date,
        description=expense.description,
        receipt_image=expense.receipt_image
    )
    
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    
    # 更新行程的实际支出
    stmt = select(func.sum(Expense.amount)).where(Expense.trip_id == trip_id)
    result = await db.execute(stmt)
    total_expense = result.scalar() or 0.0
    trip.actual_expense = total_expense
    await db.commit()
    
    return db_expense


@router.get("/", response_model=List[Expense])
async def get_trip_expenses(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取费用记录列表"""
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
    
    stmt = select(Expense).where(Expense.trip_id == trip_id)
    result = await db.execute(stmt)
    expenses = result.scalars().all()
    return expenses


@router.put("/{expense_id}", response_model=Expense)
async def update_expense(
    trip_id: int,
    expense_id: int,
    expense_update: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新费用记录"""
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
    
    # 检查费用记录是否存在
    stmt = select(Expense).where(
        Expense.id == expense_id,
        Expense.trip_id == trip_id
    )
    result = await db.execute(stmt)
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="费用记录不存在"
        )
    
    update_data = expense_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
    
    await db.commit()
    await db.refresh(expense)
    
    # 更新行程的实际支出
    stmt = select(func.sum(Expense.amount)).where(Expense.trip_id == trip_id)
    result = await db.execute(stmt)
    total_expense = result.scalar() or 0.0
    trip.actual_expense = total_expense
    await db.commit()
    
    return expense


@router.delete("/{expense_id}")
async def delete_expense(
    trip_id: int,
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除费用记录"""
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
    
    # 检查费用记录是否存在
    stmt = select(Expense).where(
        Expense.id == expense_id,
        Expense.trip_id == trip_id
    )
    result = await db.execute(stmt)
    expense = result.scalar_one_or_none()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="费用记录不存在"
        )
    
    await db.delete(expense)
    await db.commit()
    
    # 更新行程的实际支出
    stmt = select(func.sum(Expense.amount)).where(Expense.trip_id == trip_id)
    result = await db.execute(stmt)
    total_expense = result.scalar() or 0.0
    trip.actual_expense = total_expense
    await db.commit()
    
    return {"message": "费用记录删除成功"}


@router.get("/budget/analysis")
async def get_budget_analysis(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取预算分析"""
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
    
    # 按类别统计费用
    stmt = select(
        Expense.category,
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('count')
    ).where(
        Expense.trip_id == trip_id
    ).group_by(Expense.category)
    result = await db.execute(stmt)
    category_stats = result.all()
    
    # 计算总支出和预算使用率
    total_expense = sum(stat.total_amount for stat in category_stats)
    budget_usage = (total_expense / trip.total_budget * 100) if trip.total_budget > 0 else 0
    
    return {
        "trip_id": trip_id,
        "total_budget": trip.total_budget,
        "total_expense": total_expense,
        "budget_usage_percent": round(budget_usage, 2),
        "remaining_budget": trip.total_budget - total_expense,
        "category_stats": [
            {
                "category": stat.category,
                "total_amount": stat.total_amount,
                "count": stat.count,
                "percentage": round((stat.total_amount / total_expense * 100) if total_expense > 0 else 0, 2)
            }
            for stat in category_stats
        ]
    }