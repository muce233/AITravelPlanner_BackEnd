"""对话会话管理服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func
from sqlalchemy.future import select
import uuid
from datetime import datetime

from app.config import settings

from ..models.conversation import Conversation as ConversationModel, ConversationMessage, APILog
from ..schemas.chat import (
    ChatMessage, MessageRole, Conversation,
    CreateConversationRequest, UpdateConversationRequest, ConversationListResponse
)


class ConversationService:
    """对话会话管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_conversation(
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
            model=settings.chat_model,
            messages=[],
            is_active=True
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def get_conversation(self, conversation_id: str, user_id: int) -> Optional[ConversationModel]:
        """获取对话详情"""
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_conversations(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20,
        active_only: bool = True
    ) -> ConversationListResponse:
        """获取用户对话列表"""
        stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
        
        if active_only:
            stmt = stmt.where(ConversationModel.is_active == True)
        
        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # 获取分页数据
        stmt = stmt.order_by(desc(ConversationModel.updated_at)).offset(
            (page - 1) * page_size
        ).limit(page_size)
        result = await self.db.execute(stmt)
        conversations = result.scalars().all()
        
        return ConversationListResponse(
            conversations=[
                Conversation(
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
    
    async def get_or_create_conversation(
        self, 
        user_id: int, 
        title: str = "新对话"
    ) -> ConversationModel:
        """获取或创建对话"""
        # 首先尝试获取用户最近的活动对话
        stmt = select(ConversationModel).where(
            ConversationModel.user_id == user_id,
            ConversationModel.is_active == True
        ).order_by(desc(ConversationModel.updated_at)).limit(1)
        
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        # 如果没有活动对话，创建新对话
        if not conversation:
            conversation_id = str(uuid.uuid4())
            conversation = ConversationModel(
                id=conversation_id,
                title=title,
                user_id=user_id,
                model="chat-model",
                messages=[],
                is_active=True
            )
            
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
        
        return conversation
    
    async def update_conversation(
        self, 
        conversation_id: str, 
        user_id: int, 
        request: UpdateConversationRequest
    ) -> Optional[ConversationModel]:
        """更新对话信息"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        if request.title is not None:
            conversation.title = request.title
        if request.is_active is not None:
            conversation.is_active = request.is_active
        
        conversation.updated_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        """删除对话（软删除）"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        conversation.is_active = False
        conversation.updated_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(conversation)
        return True
    
    async def add_message(
        self, 
        conversation_id: str, 
        user_id: int,
        role: str, 
        content: str, 
        name: Optional[str] = None,
        tokens: Optional[int] = None
    ) -> Optional[ConversationModel]:
        """向对话添加消息（简化版本）"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        # 将消息添加到消息列表
        messages = conversation.messages or []
        messages.append({
            "role": role,
            "content": content,
            "name": name,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制消息历史长度（保留最近50条消息）
        if len(messages) > 50:
            messages = messages[-50:]
        
        conversation.messages = messages
        conversation.updated_at = datetime.now()
        
        # 如果是第一条用户消息，更新对话标题
        if len(messages) == 1 and role == "user":
            conversation.title = content[:50] + "..." if len(content) > 50 else content
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def add_message_to_conversation(
        self, 
        conversation_id: str, 
        user_id: int, 
        message: ChatMessage
    ) -> Optional[ConversationModel]:
        """向对话添加消息"""
        conversation = await self.get_conversation(conversation_id, user_id)
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
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def clear_conversation_messages(self, conversation_id: str, user_id: int) -> Optional[Conversation]:
        """清空对话消息"""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.messages = []
        conversation.updated_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation


class APILogService:
    """API调用日志服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(
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
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def get_user_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户使用统计"""
        # 今日使用量
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = select(
            APILog.prompt_tokens,
            APILog.completion_tokens,
            APILog.total_tokens,
            APILog.cost
        ).where(
            APILog.user_id == user_id,
            APILog.created_at >= today_start
        )
        today_result = await self.db.execute(today_stmt)
        today_stats = today_result.all()
        
        # 本月使用量
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_stmt = select(
            APILog.prompt_tokens,
            APILog.completion_tokens,
            APILog.total_tokens,
            APILog.cost
        ).where(
            APILog.user_id == user_id,
            APILog.created_at >= month_start
        )
        month_result = await self.db.execute(month_stmt)
        month_stats = month_result.all()
        
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
        
        # 获取总使用量
        total_stmt = select(APILog.prompt_tokens, APILog.completion_tokens, APILog.total_tokens, APILog.cost).where(
            APILog.user_id == user_id
        )
        total_result = await self.db.execute(total_stmt)
        total_stats = total_result.all()
        
        return {
            "today": calculate_stats(today_stats),
            "this_month": calculate_stats(month_stats),
            "total": calculate_stats(total_stats)
        }