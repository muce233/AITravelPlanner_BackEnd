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
        
        request_data = chat.ChatRequest(
            messages=messages
        ).model_dump(exclude_none=True)
        
        # 添加后端固定的参数
        request_data.update({
            "model": settings.chat_model,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": True
        })
        
        # 如果提供了工具定义，添加到请求中
        if tools:
            request_data["tools"] = tools
        
        print(f"DEBUG: 发送给DeepSeek API的完整请求:")
        print(f"DEBUG: URL: {self.base_url}/chat/completions")
        print(f"DEBUG: Request Data: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        try:
            async with self._client.stream(
                "POST", "/chat/completions", json=request_data
            ) as response:
                print(f"DEBUG: API响应状态码: {response.status_code}")
                print(f"DEBUG: API响应头: {dict(response.headers)}")
                
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        if data:
                            try:
                                chunk_data = json.loads(data)
                                yield chat.StreamChatResponse(**chunk_data)
                            except json.JSONDecodeError:
                                continue
        
        except HTTPStatusError as e:
            await self._handle_api_error(e)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"流式聊天API调用失败: {str(e)}"
            )
    
    async def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        # 直接从配置中获取单个模型名称
        return [settings.model]
    
    async def _handle_api_error(self, error: HTTPStatusError):
        """处理API错误"""
        try:
            error_text = await error.response.aread()
            print(f"DEBUG: API错误响应内容: {error_text.decode('utf-8', errors='ignore')}")
            error_data = error.response.json()
            error_message = error_data.get("error", {}).get("message", str(error))
        except:
            error_message = str(error)
        
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