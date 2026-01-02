# schemas包初始化文件
from .user import UserBase, UserCreate, UserUpdate, User
from .auth import LoginRequest, Token, TokenData
from .trip import TripBase, TripCreate, TripUpdate, Trip
from .trip_detail import TripDetailBase, TripDetailCreate, TripDetailUpdate, TripDetail
from .expense import ExpenseBase, ExpenseCreate, ExpenseUpdate, Expense
from .ai import TripGenerationRequest
from .speech import SpeechRecognitionRequest, SpeechRecognitionResponse
from .map import MapSearchRequest, MapDirectionsRequest
from .chat import (
    MessageRole, ChatMessage, ChatRequest, 
    ChatChoice, UsageInfo, ChatResponse, StreamChatResponse
)
from .prompt import PromptTemplate, PromptTemplateType

# 导出所有模型
__all__ = [
    # 用户相关
    "UserBase", "UserCreate", "UserUpdate", "User",
    # 认证相关
    "LoginRequest", "Token", "TokenData",
    # 行程相关
    "TripBase", "TripCreate", "TripUpdate", "Trip",
    # 行程详情
    "TripDetailBase", "TripDetailCreate", "TripDetailUpdate", "TripDetail",
    # 费用记录
    "ExpenseBase", "ExpenseCreate", "ExpenseUpdate", "Expense",
    # AI相关
    "TripGenerationRequest",
    # 语音相关
    "SpeechRecognitionRequest", "SpeechRecognitionResponse",
    # 地图相关
    "MapSearchRequest", "MapDirectionsRequest",
    # DeepSeek相关
    "DeepSeekModel", "MessageRole", "ChatMessage", "ChatRequest",
    "ChatChoice", "UsageInfo", "ChatResponse", "StreamChatResponse",
    # 提示词相关
    "PromptTemplate", "PromptTemplateType"
]