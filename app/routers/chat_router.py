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
from ..services.ai_tool_service import AiToolService
from ..services.prompt_service import prompt_service
from ..services.log_utils import get_logger
from ..schemas import chat
from ..schemas.prompt import PromptTemplateType
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
    tool_service = AiToolService(db)
    
    # 获取对话日志记录器
    conversation_logger = get_logger(
        log_dir=settings.conversation_log_dir,
        enabled=settings.enable_conversation_log
    )
    
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
        
        # 记录用户消息完整内容
        user_content = request.messages[-1].content if request.messages else ""
        conversation_logger.log(
            conversation_id=str(conversation.id),
            content=f"用户消息 - 内容: \n{user_content}"
        )
        
        # 获取系统提示词模板
        system_prompt = prompt_service.get_template(PromptTemplateType.系统提示词)
        system_content = system_prompt.template_content if system_prompt else ""
        
        # 构建消息列表，添加系统提示词
        messages = []
        if system_content:
            messages.append(chat.ChatMessage(role=chat.MessageRole.SYSTEM, content=system_content))
        messages.extend(request.messages)
        
        # 记录对话开始日志
        conversation_logger.log(
            conversation_id=str(conversation.id),
            content=f"对话开始 - 用户ID: {current_user.id}, 模型: {settings.chat_model}, 消息数量: {len(messages)}"
        )
        
        # 获取工具定义
        tools = AiToolService.get_tool_definitions()
        
        async def generate():
            full_content = ""
            tool_calls_buffer = {}
            
            try:
                # 第一次调用AI
                async for chunk in chat_service.chat_completion_stream(
                    messages=messages,
                    tools=tools
                ):
                    if chunk.choices and len(chunk.choices) > 0:
                        delta_dict = chunk.choices[0].delta
                        
                        if isinstance(delta_dict, dict):
                            content = delta_dict.get('content', '') or ""
                            tool_calls = delta_dict.get('tool_calls', None)
                        
                        # 处理文本内容
                        if content:
                            full_content += content
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
                        
                        # 处理工具调用（增量式）
                        if tool_calls and isinstance(tool_calls, list):
                            for tool_call in tool_calls:
                                if not isinstance(tool_call, dict):
                                    continue
                                
                                index = tool_call.get('index')
                                if index is None:
                                    continue
                                
                                if index not in tool_calls_buffer:
                                    tool_calls_buffer[index] = {
                                        'type': 'function',
                                        'id': tool_call.get('id', ''),
                                        'function': {
                                            'name': tool_call.get('function', {}).get('name', '') if isinstance(tool_call.get('function'), dict) else '',
                                            'arguments': tool_call.get('function', {}).get('arguments', '') if isinstance(tool_call.get('function'), dict) else ''
                                        }
                                    }
                                else:
                                    # 增量更新
                                    existing = tool_calls_buffer[index]
                                    if 'id' in tool_call and tool_call['id']:
                                        existing['id'] = tool_call['id']
                                    
                                    if 'function' in tool_call and isinstance(tool_call['function'], dict):
                                        if 'name' in tool_call['function'] and tool_call['function']['name']:
                                            existing['function']['name'] = tool_call['function']['name']
                                        if 'arguments' in tool_call['function'] and tool_call['function']['arguments']:
                                            existing['function']['arguments'] += tool_call['function']['arguments']
                    
                    # 发送心跳保持连接
                    yield "data: {}\n\n"
                
                
                # 记录普通响应完整内容
                if full_content:
                    conversation_logger.log(
                        conversation_id=str(conversation.id),
                        content=f"普通响应完整内容: \n{full_content}"
                    )
                
                # 检查是否有工具调用
                if tool_calls_buffer:
                    # 执行工具调用
                    tool_results = []
                    for index, tool_call in tool_calls_buffer.items():
                        tool_call_id = tool_call.get('id', '')
                        function = tool_call.get('function', {})
                        tool_name = function.get('name', '')
                        arguments = function.get('arguments', '')
                        
                        if not tool_name:
                            continue
                        
                        # 执行工具
                        result = await tool_service.execute_tool_call(
                            tool_call_id=tool_call_id,
                            tool_name=tool_name,
                            arguments=arguments,
                            user_id=current_user.id
                        )
                        
                        tool_results.append({
                            'tool_call_id': tool_call_id,
                            'result': result,
                            'tool_name': tool_name
                        })
                        
                        # 记录工具调用完整信息
                        conversation_logger.log(
                            conversation_id=str(conversation.id),
                            content=f"工具调用: - 工具名称: {tool_name}, 工具ID: {tool_call_id}, 完整参数: \n{arguments}"
                        )
                        
                        # 记录工具调用结果
                        conversation_logger.log(
                            conversation_id=str(conversation.id),
                            content=f"工具调用结果: - 工具名称: {tool_name}, 结果: \n{json.dumps(result.dict(), ensure_ascii=False)}"
                        )
                        
                        # 保存工具调用消息到对话
                        await conversation_service.add_message(
                            conversation_id=conversation.id,
                            user_id=current_user.id,
                            role="assistant",
                            content=json.dumps({"tool_calls": [tool_call]}),
                            name="assistant"
                        )
                        
                        # 保存工具结果消息到对话
                        await conversation_service.add_message(
                            conversation_id=conversation.id,
                            user_id=current_user.id,
                            role="tool",
                            content=json.dumps(result.dict()),
                            name=tool_name
                        )
                    
                    # 根据阿里云Function Calling规范，消息序列必须是：
                    # user -> assistant(包含tool_calls) -> tool(包含tool_call_id)
                    # 所以需要先添加包含tool_calls的assistant消息，再添加tool消息
                    
                    # 1. 将tool_calls_buffer转换为列表格式
                    tool_calls_list = list(tool_calls_buffer.values())
                    
                    # 2. 添加包含tool_calls的assistant消息
                    assistant_tool_calls_message = chat.ChatMessage(
                        role=chat.MessageRole.ASSISTANT,
                        content="",
                        tool_calls=tool_calls_list
                    )
                    messages.append(assistant_tool_calls_message)
                    
                    # 2. 将工具调用结果添加到消息历史
                    for tool_result in tool_results:
                        tool_message = chat.ChatMessage(
                            role=chat.MessageRole.TOOL,
                            content=json.dumps(tool_result['result'].dict()),
                            tool_call_id=tool_result['tool_call_id']
                        )
                        messages.append(tool_message)
                    
                    # 再次调用AI，获取最终回复
                    assistant_response_content = ""
                    async for chunk in chat_service.chat_completion_stream(
                        messages=messages,
                        tools=tools
                    ):
                        if chunk.choices and chunk.choices[0].delta:
                            delta_dict = chunk.choices[0].delta
                            content = delta_dict.get('content', '') or ""
                            
                            if content:
                                assistant_response_content += content
                                full_content += content
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
                        
                        yield "data: {}\n\n"
                    
                    # 记录工具调用后响应完整内容
                    if assistant_response_content:
                        conversation_logger.log(
                            conversation_id=str(conversation.id),
                            content=f"工具调用后响应完整内容: \n{assistant_response_content}"
                        )
                    
                    # 保存AI最终回复到对话
                    if assistant_response_content:
                        await conversation_service.add_message(
                            conversation_id=conversation.id,
                            user_id=current_user.id,
                            role="assistant",
                            content=assistant_response_content,
                            name="assistant"
                        )
                else:
                    # 没有工具调用，直接保存AI回复
                    if full_content:
                        await conversation_service.add_message(
                            conversation_id=conversation.id,
                            user_id=current_user.id,
                            role="assistant",
                            content=full_content,
                            name="assistant"
                        )
                
                # 记录对话结束日志
                response_time = int((time.time() - start_time) * 1000)
                conversation_logger.log(
                    conversation_id=str(conversation.id),
                    content=f"对话结束 - 总耗时: {response_time}ms, 总内容长度: {len(full_content)}"
                )
                
                # 记录API日志
                response_time = int((time.time() - start_time) * 1000)
                await api_log_service.create_log(
                    user_id=current_user.id,
                    endpoint="chat/completions/stream",
                    model=settings.chat_model,
                    response_time=response_time,
                    status_code=200
                )
                
                # 发送结束信号
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                # 记录错误日志
                conversation_logger.log(
                    conversation_id=str(conversation.id),
                    content=f"错误 - 错误类型: {type(e).__name__}, 错误信息: {str(e)}"
                )
                
                # 记录错误日志
                response_time = int((time.time() - start_time) * 1000)
                await api_log_service.create_log(
                    user_id=current_user.id,
                    endpoint="chat/completions/stream",
                    model=settings.chat_model,
                    response_time=response_time,
                    status_code=500,
                    error_message=str(e)
                )
                
                # 发送错误信号
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
            finally:
                pass
        
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
        conversation_logger.log(
            conversation_id=str(conversation.id) if 'conversation' in locals() else "unknown",
            content=f"错误 - 错误类型: {type(e).__name__}, 错误信息: {str(e)}"
        )
        
        # 记录错误日志
        response_time = int((time.time() - start_time) * 1000)
        await api_log_service.create_log(
            user_id=current_user.id,
            endpoint="chat/completions/stream",
            model=settings.chat_model,
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