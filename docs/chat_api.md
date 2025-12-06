# 聊天API 接口文档

## 概述

聊天API 提供了与AI大语言模型进行对话交互的能力，支持流式响应和完整响应两种模式，包含对话历史管理、上下文维护等功能。

## 基础信息

- **基础URL**: `/api/chat`
- **认证方式**: Bearer Token (JWT)
- **响应格式**: JSON
- **流式响应**: Server-Sent Events (SSE)

## 认证

所有API请求都需要在Header中携带JWT令牌：

```http
Authorization: Bearer <your_jwt_token>
```

## 错误码对照表

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式和类型 |
| 401 | 未授权访问 | 检查JWT令牌是否有效 |
| 404 | 资源不存在 | 检查请求的资源ID是否正确 |
| 429 | 请求频率超限 | 降低请求频率或等待限流重置 |
| 500 | 服务器内部错误 | 联系系统管理员 |

## API端点

### 1. 获取API状态

**GET** `/api/chat/status`

获取API服务状态和可用模型列表。

**响应示例**:
```json
{
  "status": "active",
  "version": "1.0.0",
  "models": [
    "chat-model",
    "coder-model",
    "reasoner-model"
  ],
  "rate_limit": {
    "requests_per_minute": 1000,
    "remaining_requests": 950
  }
}
```

### 2. 获取模型列表

**GET** `/api/chat/models`

获取所有可用的AI模型列表。

**响应示例**:
```json
{
  "data": [
    {
      "id": "chat-model",
      "object": "model",
      "created": 1700000000,
      "owned_by": "chat-service"
    },
    {
      "id": "coder-model",
      "object": "model",
      "created": 1700000000,
      "owned_by": "chat-service"
    }
  ]
}
```

### 3. 创建聊天补全（非流式）

**POST** `/api/chat/completions`

创建聊天补全请求，返回完整的响应。

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请帮我规划一个三天的北京旅行行程"
    }
  ],
  "model": "chat-model",
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

**响应示例**:
```json
{
  "id": "chatcmpl-123456789",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "chat-model",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "好的，我来为您规划一个三天的北京旅行行程..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 450,
    "total_tokens": 475
  }
}
```

### 4. 创建聊天补全（流式）

**POST** `/api/chat/completions/stream`

创建流式聊天补全请求，通过SSE实时返回响应内容。

**请求体**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "请用中文回答"
    }
  ],
  "model": "chat-model",
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": true
}
```

**响应格式**:
```
data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1700000000, "model": "chat-model", "choices": [{"index": 0, "delta": {"content": "好的"}, "finish_reason": null}]}

data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1700000000, "model": "chat-model", "choices": [{"index": 0, "delta": {"content": "，"}, "finish_reason": null}]}

data: [DONE]
```

## 数据模型

### ChatMessage
```typescript
{
  role: "user" | "assistant" | "system",
  content: string,
  name?: string
}
```

### ChatRequest
```typescript
{
  messages: ChatMessage[],
  model: string,
  temperature?: number,
  max_tokens?: number,
  top_p?: number,
  frequency_penalty?: number,
  presence_penalty?: number,
  stop?: string[],
  stream?: boolean,
  user?: string
}
```

### ChatResponse
```typescript
{
  id: string,
  object: "chat.completion",
  created: number,
  model: string,
  choices: [{
    index: number,
    message: ChatMessage,
    finish_reason: string
  }],
  usage: {
    prompt_tokens: number,
    completion_tokens: number,
    total_tokens: number
  }
}
```

## 使用示例

### JavaScript 示例
```javascript
// 获取API状态
const response = await fetch('/api/chat/status', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});

// 发送聊天请求
const chatResponse = await fetch('/api/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: '你好' }],
    model: 'chat-model'
  })
});
```

### Python 示例
```python
import requests

# 获取API状态
response = requests.get(
    '/api/chat/status',
    headers={'Authorization': f'Bearer {token}'}
)

# 发送聊天请求
chat_response = requests.post(
    '/api/chat/completions',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    json={
        'messages': [{'role': 'user', 'content': '你好'}],
        'model': 'chat-model'
    }
)
```

## 限流策略

- 每个用户每分钟最多1000次请求
- 超过限制会返回429状态码
- 建议在客户端实现请求队列和重试机制

## 注意事项

1. 所有请求都需要有效的JWT令牌
2. 流式响应需要客户端支持SSE协议
3. 建议设置合理的超时时间（30秒）
4. 对话历史会自动保存在服务器端
5. 支持多轮对话上下文管理