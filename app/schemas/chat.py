"""聊天API相关数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class ChatModel(str, Enum):
    """聊天可用模型枚举"""
    CHAT_MODEL = "chat-model"
    CODER_MODEL = "coder-model"
    REASONER_MODEL = "reasoner-model"


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="消息发送者名称")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage] = Field(..., description="消息历史列表")
    model: ChatModel = Field(default=ChatModel.CHAT_MODEL, description="使用的模型")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=8192, description="最大生成token数")
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0, description="Top-p采样参数")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop: Optional[List[str]] = Field(default=None, description="停止序列")
    stream: Optional[bool] = Field(default=False, description="是否启用流式响应")
    user: Optional[str] = Field(default=None, description="用户标识")


class ChatChoice(BaseModel):
    """聊天选择项模型"""
    index: int = Field(..., description="选择项索引")
    message: ChatMessage = Field(..., description="AI回复消息")
    finish_reason: Optional[str] = Field(None, description="完成原因")


class UsageInfo(BaseModel):
    """使用量信息模型"""
    prompt_tokens: int = Field(..., description="提示token数")
    completion_tokens: int = Field(..., description="完成token数")
    total_tokens: int = Field(..., description="总token数")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatChoice] = Field(..., description="选择项列表")
    usage: UsageInfo = Field(..., description="使用量信息")


class StreamChatChoice(BaseModel):
    """流式聊天选择项模型"""
    index: int = Field(..., description="选择项索引")
    delta: Dict[str, Any] = Field(..., description="增量内容")
    finish_reason: Optional[str] = Field(None, description="完成原因")


class StreamChatResponse(BaseModel):
    """流式聊天响应模型"""
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion.chunk", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[StreamChatChoice] = Field(..., description="选择项列表")


class Conversation(BaseModel):
    """对话会话模型"""
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    user_id: int = Field(..., description="用户ID")
    messages: List[ChatMessage] = Field(default=[], description="消息列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    model: ChatModel = Field(default=ChatModel.CHAT_MODEL, description="使用的模型")
    is_active: bool = Field(default=True, description="是否活跃")


class CreateConversationRequest(BaseModel):
    """创建对话请求模型"""
    title: str = Field(..., description="会话标题")
    model: Optional[ChatModel] = Field(default=ChatModel.CHAT_MODEL, description="使用的模型")


class UpdateConversationRequest(BaseModel):
    """更新对话请求模型"""
    title: Optional[str] = Field(None, description="会话标题")
    is_active: Optional[bool] = Field(None, description="是否活跃")


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    user_id: int = Field(..., description="用户ID")
    messages: List[ChatMessage] = Field(default=[], description="消息列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    model: ChatModel = Field(..., description="使用的模型")
    is_active: bool = Field(..., description="是否活跃")


class APIStatusResponse(BaseModel):
    """API状态响应模型"""
    status: str = Field(..., description="API状态")
    version: str = Field(..., description="API版本")
    models: List[str] = Field(..., description="可用模型列表")


class ModelsResponse(BaseModel):
    """模型列表响应模型"""
    data: List[Dict[str, Any]] = Field(..., description="模型列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    code: Optional[int] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class ConversationListResponse(BaseModel):
    """对话列表响应模型"""
    conversations: List[Conversation] = Field(..., description="对话列表")
    total: int = Field(..., description="总对话数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")