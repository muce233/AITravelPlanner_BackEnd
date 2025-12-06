from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "AI Travel Planner API"
    debug: bool = False
    
    # 数据库配置
    database_url: str
    
    # JWT配置
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI服务配置
    openai_api_key: Optional[str] = None
    ai_service_url: str = "https://api.openai.com/v1"
    
    # 聊天API配置
    chat_api_key: Optional[str] = None
    chat_api_url: str = "https://api.deepseek.com/v1"
    
    # 语音识别服务配置
    speech_recognition_api_key: Optional[str] = None
    speech_service_url: str = "https://api.xfyun.cn/v1"
    
    # 地图服务配置
    amap_api_key: Optional[str] = None
    
    # API限流配置
    rate_limit_requests: int = 1000  # 每分钟请求限制
    rate_limit_window: int = 60  # 时间窗口（秒）
    
    # CORS配置
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()