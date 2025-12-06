"""请求限流中间件"""
import time
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from ..config import settings

# 创建限流器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/minute"]
)


def setup_rate_limit_middleware(app):
    """设置限流中间件"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def get_rate_limit_info(request: Request) -> dict:
    """获取限流信息"""
    if hasattr(request.state, "rate_limit"):
        return request.state.rate_limit
    
    # 默认返回空信息
    return {
        "limit": settings.rate_limit_requests,
        "remaining": settings.rate_limit_requests,
        "reset_time": 0
    }


class UserRateLimiter:
    """基于用户的限流器"""
    
    def __init__(self):
        self.user_limits = {}
    
    def check_rate_limit(self, user_id: int, endpoint: str) -> bool:
        """检查用户请求频率"""
        key = f"{user_id}:{endpoint}"
        current_time = time.time()
        
        if key not in self.user_limits:
            self.user_limits[key] = {
                "count": 0,
                "window_start": current_time
            }
        
        limit_info = self.user_limits[key]
        
        # 检查时间窗口是否过期
        if current_time - limit_info["window_start"] > settings.rate_limit_window:
            limit_info["count"] = 0
            limit_info["window_start"] = current_time
        
        # 检查是否超过限制
        if limit_info["count"] >= settings.rate_limit_requests:
            return False
        
        limit_info["count"] += 1
        return True
    
    def get_remaining_requests(self, user_id: int, endpoint: str) -> int:
        """获取剩余请求次数"""
        key = f"{user_id}:{endpoint}"
        
        if key not in self.user_limits:
            return settings.rate_limit_requests
        
        limit_info = self.user_limits[key]
        current_time = time.time()
        
        # 检查时间窗口是否过期
        if current_time - limit_info["window_start"] > settings.rate_limit_window:
            return settings.rate_limit_requests
        
        return max(0, settings.rate_limit_requests - limit_info["count"])


# 全局用户限流器实例
user_rate_limiter = UserRateLimiter()