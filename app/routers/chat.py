"""聊天API路由"""
import time
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_active_user
from ..database import get_db
from ..models import User as UserModel
from ..services.chat_client import chat_service
from ..services.conversation_service import ConversationService, APILogService
from ..schemas import chat
from ..middleware.rate_limit import user_rate_limiter
from ..config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])








@router.post("/completions/stream")
async def create_chat_completion_stream(
    request: chat.ChatRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建聊天补全（流式）"""
    start_time = time.time()
    
    # 检查用户请求频率
    if not user_rate_limiter.check_rate_limit(current_user.id, "chat/completions/stream"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求频率过高，请稍后再试"
        )
    
    conversation_service = ConversationService(db)
    api_log_service = APILogService(db)
    
    try:
        # 创建或获取对话
        conversation = await conversation_service.get_or_create_conversation(
            user_id=current_user.id,
            title=request.messages[0].content[:50] if request.messages else "新对话"
        )
        
        # 添加用户消息到对话
        user_message = await conversation_service.add_message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="user",
            content=request.messages[-1].content if request.messages else "",
            name=request.messages[-1].name if request.messages and hasattr(request.messages[-1], 'name') else None
        )
        
        async def generate():
            full_content = ""
            
            try:
                async for chunk in chat_service.chat_completion_stream(
                    messages=request.messages
                ):
                    if chunk.choices and chunk.choices[0].delta:
                        # 正确访问字典类型的delta字段
                        delta_dict = chunk.choices[0].delta
                        content = delta_dict.get('content', '') or ""
                        full_content += content
                        
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({
                            'id': chunk.id,
                            'object': chunk.object,
                            'created': chunk.created,
                            'model': chunk.model,
                            'choices': [{
                                'index': chunk.choices[0].index,
                                'delta': delta_dict,
                                'finish_reason': chunk.choices[0].finish_reason
                            }]
                        })}\n\n"
                    
                    # 发送心跳保持连接
                    yield "data: {}\n\n"
                
                # 添加AI回复到对话
                ai_message = await conversation_service.add_message(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    role="assistant",
                    content=full_content,
                    tokens=len(full_content) // 4  # 粗略估算token数量
                )
                
                # 记录API日志
                response_time = int((time.time() - start_time) * 1000)
                await api_log_service.create_log(
                    user_id=current_user.id,
                    endpoint="chat/completions/stream",
                    model=request.model,
                    response_time=response_time,
                    status_code=200
                )
                
                # 发送结束信号
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                # 即使流式响应失败，也要保存已收到的内容
                if full_content:
                    ai_message = await conversation_service.add_message(
                        conversation_id=conversation.id,
                        user_id=current_user.id,
                        role="assistant",
                        content=full_content,
                        tokens=len(full_content) // 4
                    )
                
                # 记录错误日志
                response_time = int((time.time() - start_time) * 1000)
                await api_log_service.create_log(
                    user_id=current_user.id,
                    endpoint="chat/completions/stream",
                    model=request.model,
                    response_time=response_time,
                    status_code=500,
                    error_message=str(e)
                )
                
                # 发送错误信号
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        # 记录错误日志
        response_time = int((time.time() - start_time) * 1000)
        await api_log_service.create_log(
            user_id=current_user.id,
            endpoint="chat/completions/stream",
            model=request.model if 'request' in locals() else None,
            response_time=response_time,
            status_code=500,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式聊天请求失败: {str(e)}"
        )





# 对话管理接口
@router.get("/conversations", response_model=chat.ConversationListResponse)
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户对话列表"""
    try:
        conversation_service = ConversationService(db)
        return await conversation_service.get_user_conversations(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话列表失败: {str(e)}"
        )


@router.post("/conversations", response_model=chat.Conversation)
async def create_conversation(
    request: chat.CreateConversationRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.create_conversation(
            user_id=current_user.id,
            request=request
        )
        
        return chat.Conversation(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            messages=[],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            model=conversation.model,
            is_active=conversation.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建对话失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=chat.Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话详情"""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话失败: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=chat.Conversation)
async def update_conversation(
    conversation_id: str,
    request: chat.UpdateConversationRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新对话信息"""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            request=request
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        # 获取更新后的对话详情（包含消息）
        conversation_with_messages = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        return conversation_with_messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新对话失败: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除对话（软删除）"""
    try:
        conversation_service = ConversationService(db)
        success = await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        return {"message": "对话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除对话失败: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation_messages(
    conversation_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """清空对话消息"""
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.clear_conversation_messages(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        return {"message": "对话消息清空成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空对话消息失败: {str(e)}"
        )