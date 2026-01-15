from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database import get_db
from ..auth import get_current_active_user
from ..models import User as UserModel
from ..schemas.user import User, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/login")
def login_user():
    """用户登录（实际登录逻辑在auth路由中实现）"""
    return {"message": "请使用 /api/auth/login 端点进行登录"}


@router.get("/profile", response_model=User)
def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """获取用户信息"""
    return current_user


@router.put("/profile", response_model=User)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    update_data = user_update.dict(exclude_unset=True)
    
    # 如果更新用户名，检查是否重复
    if "username" in update_data and update_data["username"] != current_user.username:
        stmt = select(UserModel).where(UserModel.username == update_data["username"])
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 如果更新手机号，检查是否重复
    if "phone_number" in update_data and update_data["phone_number"] != current_user.phone_number:
        stmt = select(UserModel).where(UserModel.phone_number == update_data["phone_number"])
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号已注册"
            )
    
    # 更新用户信息
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user