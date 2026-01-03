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
        
        # 获取系统提示词模板
        system_prompt = prompt_service.get_template(PromptTemplateType.系统提示词)
        system_content = system_prompt.template_content if system_prompt else ""
        
        print(f"DEBUG: 系统提示词内容:")
        print(f"DEBUG: {system_content}")
        
        # 构建消息列表，添加系统提示词
        messages = []
        if system_content:
            messages.append(chat.ChatMessage(role=chat.MessageRole.SYSTEM, content=system_content))
        messages.extend(request.messages)
        
        print(f"DEBUG: 发送给AI的消息列表:")
        for i, msg in enumerate(messages):
            print(f"DEBUG: 消息{i}: role={msg.role}, content={msg.content[:100] if msg.content else ''}")
        
        # 获取工具定义
        tools = AiToolService.get_tool_definitions()
        
        print(f"DEBUG: 工具定义:")
        print(f"DEBUG: {json.dumps(tools, ensure_ascii=False, indent=2)}")
        
        async def generate():
            full_content = ""
            tool_calls_buffer = {}
            
            try:
                # 第一次调用AI
                async for chunk in chat_service.chat_completion_stream(
                    messages=messages,
                    tools=tools
                ):
                    print(f"DEBUG: chunk类型: {type(chunk)}")
                    print(f"DEBUG: chunk: {chunk}")
                    
                    if chunk.choices and len(chunk.choices) > 0:
                        print(f"DEBUG: chunk.choices[0]: {chunk.choices[0]}")
                        print(f"DEBUG: chunk.choices[0].delta: {chunk.choices[0].delta}")
                        print(f"DEBUG: chunk.choices[0].delta类型: {type(chunk.choices[0].delta)}")
                        
                        delta_dict = chunk.choices[0].delta
                        
                        if isinstance(delta_dict, dict):
                            content = delta_dict.get('content', '') or ""
                            tool_calls = delta_dict.get('tool_calls', None)
                            
                            print(f"DEBUG: content: {content}")
                            print(f"DEBUG: tool_calls: {tool_calls}")
                            print(f"DEBUG: tool_calls类型: {type(tool_calls)}")
                        
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
                            print(f"DEBUG: 收到工具调用: {tool_calls}")
                            for tool_call in tool_calls:
                                if not isinstance(tool_call, dict):
                                    print(f"DEBUG: tool_call 不是字典类型: {type(tool_call)}")
                                    continue
                                
                                index = tool_call.get('index')
                                if index is None:
                                    print(f"DEBUG: tool_call 缺少 index 字段")
                                    continue
                                
                                if index not in tool_calls_buffer:
                                    tool_calls_buffer[index] = {
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
                                
                                print(f"DEBUG: 累积后的 tool_calls_buffer[{index}]: {tool_calls_buffer[index]}")
                    
                    # 发送心跳保持连接
                    yield "data: {}\n\n"
                
                print(f"DEBUG: 最终 tool_calls_buffer: {tool_calls_buffer}")
                
                # 检查是否有工具调用
                if tool_calls_buffer:
                    # 执行工具调用
                    tool_results = []
                    for index, tool_call in tool_calls_buffer.items():
                        tool_call_id = tool_call.get('id', '')
                        function = tool_call.get('function', {})
                        tool_name = function.get('name', '')
                        arguments = function.get('arguments', '')
                        
                        print(f"DEBUG: 执行工具调用 - tool_call_id: {tool_call_id}, tool_name: {tool_name}, arguments: {arguments}")
                        
                        if not tool_name:
                            print(f"DEBUG: 警告 - tool_name 为空")
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
                    
                    # 将工具调用结果添加到消息历史
                    for tool_result in tool_results:
                        messages.append(chat.ChatMessage(
                            role=chat.MessageRole.TOOL,
                            content=json.dumps(tool_result['result'].dict()),
                            name=tool_result['tool_name']
                        ))
                    
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