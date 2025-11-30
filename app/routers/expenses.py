from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_active_user
from ..models import Trip, Expense, User
from ..schemas import Expense, ExpenseCreate, ExpenseUpdate

router = APIRouter(prefix="/api/trips/{trip_id}/expenses", tags=["expenses"])


@router.post("/", response_model=Expense)
def create_expense(
    trip_id: int,
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """添加费用记录"""
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
    db.commit()
    db.refresh(db_expense)
    
    # 更新行程的实际支出
    total_expense = db.query(db.func.sum(Expense.amount)).filter(Expense.trip_id == trip_id).scalar() or 0.0
    trip.actual_expense = total_expense
    db.commit()
    
    return db_expense


@router.get("/", response_model=List[Expense])
def get_trip_expenses(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取费用记录列表"""
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
    
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    return expenses


@router.put("/{expense_id}", response_model=Expense)
def update_expense(
    trip_id: int,
    expense_id: int,
    expense_update: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新费用记录"""
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
    
    # 检查费用记录是否存在
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.trip_id == trip_id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="费用记录不存在"
        )
    
    update_data = expense_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
    
    db.commit()
    db.refresh(expense)
    
    # 更新行程的实际支出
    total_expense = db.query(db.func.sum(Expense.amount)).filter(Expense.trip_id == trip_id).scalar() or 0.0
    trip.actual_expense = total_expense
    db.commit()
    
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    trip_id: int,
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除费用记录"""
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
    
    # 检查费用记录是否存在
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.trip_id == trip_id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="费用记录不存在"
        )
    
    db.delete(expense)
    db.commit()
    
    # 更新行程的实际支出
    total_expense = db.query(db.func.sum(Expense.amount)).filter(Expense.trip_id == trip_id).scalar() or 0.0
    trip.actual_expense = total_expense
    db.commit()
    
    return {"message": "费用记录删除成功"}


@router.get("/budget/analysis")
def get_budget_analysis(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取预算分析"""
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
    
    # 按类别统计费用
    category_stats = db.query(
        Expense.category,
        db.func.sum(Expense.amount).label('total_amount'),
        db.func.count(Expense.id).label('count')
    ).filter(
        Expense.trip_id == trip_id
    ).group_by(Expense.category).all()
    
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