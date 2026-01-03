"""聊天API客户端封装"""
import asyncio
import json
import uuid
import time
from typing import Optional, AsyncGenerator, Dict, Any
from httpx import AsyncClient, Timeout, HTTPStatusError
from fastapi import HTTPException, status

from ..config import settings
from ..schemas import chat


class ChatClient:
    """聊天API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.chat_api_key
        self.base_url = settings.chat_api_url
        self.timeout = Timeout(30.0)
        self._client: Optional[AsyncClient] = None
        
    async def __aenter__(self):
        await self._initialize_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def _initialize_client(self):
        """初始化HTTP客户端"""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            self._client = AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    

    
    async def chat_completion_stream(
        self,
        messages: list[chat.ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """流式聊天补全接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表，用于Function Calling
        
        Yields:
            StreamChatResponse: 流式响应块
        """
        await self._initialize_client()
        
        # 将 ChatMessage 对象列表转换为 API 需要的格式
        messages_data = []
        for msg in messages:
            msg_dict = {
                "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                "content": msg.content
            }
            # 只有当 name 不为 None 时才添加
            if msg.name is not None:
                msg_dict["name"] = msg.name
            # 只有当 tool_call_id 不为 None 时才添加（用于tool角色的消息）
            if msg.tool_call_id is not None:
                msg_dict["tool_call_id"] = msg.tool_call_id
            # 只有当 tool_calls 不为 None 时才添加（用于assistant角色的消息）
            if msg.tool_calls is not None:
                msg_dict["tool_calls"] = msg.tool_calls
            messages_data.append(msg_dict)
        
        # 构建请求数据
        request_data = {
            "messages": messages_data,
            "model": settings.chat_model,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True
        }
        
        # 如果提供了工具定义，添加到请求中
        if tools:
            request_data["tools"] = tools
        
        # 打印详细的请求信息
        print("=" * 80)
        print("DEBUG: 准备发送API请求")
        print(f"DEBUG: 请求URL: {self.base_url}/chat/completions")
        print(f"DEBUG: 请求方法: POST")
        print(f"DEBUG: 请求头: Content-Type: application/json, Authorization: Bearer {self.api_key[:10]}...")
        print(f"DEBUG: 请求体:")
        print(json.dumps(request_data, ensure_ascii=False, indent=2))
        print("=" * 80)
        
        # 收集调试信息
        debug_info = {
            "request_url": f"{self.base_url}/chat/completions",
            "request_data": request_data,
            "chunks_received": 0,
            "total_content_length": 0,
            "tool_calls_count": 0,
            "response_status": None,
            "response_headers": None
        }
        
        error_message = None
        
        try:
            async with self._client.stream(
                "POST", "/chat/completions", content=json.dumps(request_data, ensure_ascii=False)
            ) as response:
                debug_info["response_status"] = response.status_code
                debug_info["response_headers"] = dict(response.headers)
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_text_str = error_text.decode('utf-8', errors='ignore')
                    print(f"DEBUG: API错误响应内容: {error_text_str}")
                    print("=" * 80)
                    try:
                        error_data = json.loads(error_text_str)
                        error_message = error_data.get("error", {}).get("message", error_text_str)
                    except:
                        error_message = error_text_str
                    response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        if data:
                            try:
                                chunk_data = json.loads(data)
                                debug_info["chunks_received"] += 1
                                
                                # 统计内容长度
                                if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        debug_info["total_content_length"] += len(content)
                                    
                                    # 统计工具调用
                                    tool_calls = delta.get("tool_calls")
                                    if tool_calls:
                                        debug_info["tool_calls_count"] += len(tool_calls)
                                
                                yield chat.StreamChatResponse(**chunk_data)
                            except json.JSONDecodeError:
                                continue
                
                # 流式响应完成后打印汇总日志
                print(f"DEBUG: 流式响应完成 - URL: {debug_info['request_url']}")
                print(f"DEBUG: 请求数据: {json.dumps(debug_info['request_data'], ensure_ascii=False, indent=2)}")
                print(f"DEBUG: 响应状态码: {debug_info['response_status']}")
                print(f"DEBUG: 接收到的chunk数量: {debug_info['chunks_received']}")
                print(f"DEBUG: 总内容长度: {debug_info['total_content_length']} 字符")
                print(f"DEBUG: 工具调用次数: {debug_info['tool_calls_count']}")
        
        except HTTPStatusError as e:
            await self._handle_api_error(e, error_message)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"流式聊天API调用失败: {str(e)}"
            )
    
    async def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        # 直接从配置中获取单个模型名称
        return [settings.model]
    
    async def _handle_api_error(self, error: HTTPStatusError, error_message: Optional[str] = None):
        """处理API错误"""
        print("=" * 80)
        print(f"DEBUG: API错误发生")
        print(f"DEBUG: 错误状态码: {error.response.status_code}")
        print(f"DEBUG: 错误URL: {error.request.url}")
        print(f"DEBUG: 错误方法: {error.request.method}")
        print(f"DEBUG: 请求头: {dict(error.request.headers)}")
        print(f"DEBUG: 请求体: {error.request.content}")
        print("=" * 80)
        
        if error_message is None:
            try:
                error_text = await error.response.aread()
                error_text_str = error_text.decode('utf-8', errors='ignore')
                print(f"DEBUG: API错误响应内容: {error_text_str}")
                print("=" * 80)
                error_data = error.response.json()
                error_message = error_data.get("error", {}).get("message", str(error))
                print(f"DEBUG: 解析后的错误信息: {error_message}")
                print("=" * 80)
            except Exception as parse_error:
                print(f"DEBUG: 解析错误响应失败: {parse_error}")
                error_message = str(error)
                print(f"DEBUG: 使用原始错误信息: {error_message}")
                print("=" * 80)
        else:
            print(f"DEBUG: 使用已捕获的错误信息: {error_message}")
            print("=" * 80)
        
        if error.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"API密钥无效: {error_message}"
            )
        elif error.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"API请求频率限制: {error_message}"
            )
        elif error.response.status_code >= 500:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"聊天服务暂时不可用: {error_message}"
            )
        else:
            raise HTTPException(
                status_code=error.response.status_code,
                detail=f"聊天API错误: {error_message}"
            )


# 创建全局聊天服务实例
chat_service = ChatClient()