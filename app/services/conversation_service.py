"""对话会话管理服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
from datetime import datetime

from ..models.conversation import Conversation as ConversationModel, ConversationMessage, APILog
from ..schemas.chat import (
    ChatMessage, MessageRole, ChatModel, Conversation,
    CreateConversationRequest, UpdateConversationRequest, ConversationListResponse
)


class ConversationService:
    """对话会话服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(
        self, 
        user_id: int, 
        request: CreateConversationRequest
    ) -> ConversationModel:
        """创建新对话"""
        conversation_id = str(uuid.uuid4())
        
        conversation = ConversationModel(
            id=conversation_id,
            title=request.title,
            user_id=user_id,
            model=request.model.value if request.model else ChatModel.CHAT_MODEL.value,
            messages=[],
            is_active=True
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str, user_id: int) -> Optional[ConversationModel]:
        """获取对话详情"""
        return self.db.query(ConversationModel).filter(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id
        ).first()
    
    def get_user_conversations(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20,
        active_only: bool = True
    ) -> ConversationListResponse:
        """获取用户对话列表"""
        query = self.db.query(ConversationModel).filter(ConversationModel.user_id == user_id)
        
        if active_only:
            query = query.filter(ConversationModel.is_active == True)
        
        total = query.count()
        conversations = query.order_by(desc(ConversationModel.updated_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return ConversationListResponse(
            conversations=[
                chat.Conversation(
                    id=conv.id,
                    title=conv.title,
                    user_id=conv.user_id,
                    messages=[
                        ChatMessage(role=MessageRole(msg["role"]), content=msg["content"])
                        for msg in conv.messages
                    ],
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    model=conv.model,
                    is_active=conv.is_active
                ) for conv in conversations
            ],
            total=total,
            page=page,
            page_size=page_size
        )
    
    def update_conversation(
        self, 
        conversation_id: str, 
        user_id: int, 
        request: UpdateConversationRequest
    ) -> Optional[ConversationModel]:
        """更新对话信息"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        if request.title is not None:
            conversation.title = request.title
        if request.is_active is not None:
            conversation.is_active = request.is_active
        
        conversation.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        """删除对话（软删除）"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        conversation.is_active = False
        conversation.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(conversation)
        return True
    
    def add_message_to_conversation(
        self, 
        conversation_id: str, 
        user_id: int, 
        message: ChatMessage
    ) -> Optional[ConversationModel]:
        """向对话添加消息"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        # 将消息添加到消息列表
        messages = conversation.messages or []
        messages.append({
            "role": message.role.value,
            "content": message.content,
            "name": message.name,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制消息历史长度（保留最近50条消息）
        if len(messages) > 50:
            messages = messages[-50:]
        
        conversation.messages = messages
        conversation.updated_at = datetime.now()
        
        # 如果是第一条用户消息，更新对话标题
        if len(messages) == 1 and message.role == MessageRole.USER:
            conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def clear_conversation_messages(self, conversation_id: str, user_id: int) -> Optional[Conversation]:
        """清空对话消息"""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.messages = []
        conversation.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation


class APILogService:
    """API调用日志服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_api_call(
        self,
        user_id: int,
        endpoint: str,
        model: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost: int = 0,
        response_time: Optional[int] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> APILog:
        """记录API调用日志"""
        log = APILog(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            response_time=response_time,
            status_code=status_code,
            error_message=error_message
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def get_user_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户使用统计"""
        # 今日使用量
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = self.db.query(
            APILog.prompt_tokens,
            APILog.completion_tokens,
            APILog.total_tokens,
            APILog.cost
        ).filter(
            APILog.user_id == user_id,
            APILog.created_at >= today_start
        ).all()
        
        # 本月使用量
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_stats = self.db.query(
            APILog.prompt_tokens,
            APILog.completion_tokens,
            APILog.total_tokens,
            APILog.cost
        ).filter(
            APILog.user_id == user_id,
            APILog.created_at >= month_start
        ).all()
        
        def calculate_stats(stats_list):
            if not stats_list:
                return {"total_tokens": 0, "total_cost": 0, "call_count": 0}
            
            total_prompt = sum(stat.prompt_tokens for stat in stats_list)
            total_completion = sum(stat.completion_tokens for stat in stats_list)
            total_tokens = sum(stat.total_tokens for stat in stats_list)
            total_cost = sum(stat.cost for stat in stats_list)
            
            return {
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_completion,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "call_count": len(stats_list)
            }
        
        return {
            "today": calculate_stats(today_stats),
            "this_month": calculate_stats(month_stats),
            "total": calculate_stats(self.db.query(APILog).filter(APILog.user_id == user_id).all())
        }