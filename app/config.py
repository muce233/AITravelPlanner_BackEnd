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
    
    # 聊天API配置
    chat_api_key: Optional[str] = None
    chat_api_url: str = "https://api.deepseek.com/v1"
    chat_model: str = "deepseek-chat"
    
    # 阿里百炼语音识别配置
    dashscope_api_key: Optional[str] = None
    dashscope_speech_model: str = "fun-asr-realtime"
    fun_asr_url: str = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    vad_enabled: bool = True
    
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