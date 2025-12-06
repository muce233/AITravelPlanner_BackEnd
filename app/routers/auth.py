from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..auth import authenticate_user, create_access_token
from ..config import settings
from ..schemas import Token, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录获取访问令牌"""
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user():
    """用户登出"""
    # 在实际应用中，可能需要将令牌加入黑名单
    return {"message": "登出成功"}