# AI旅行规划助手 - 详细API接口规范

## 认证相关接口 (Authentication)

### POST /api/auth/login
**用户登录获取访问令牌**

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应体 (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

**错误响应:**
- `401 Unauthorized`: 用户名或密码错误

### POST /api/auth/logout
**用户登出**

**响应体 (200):**
```json
{
  "message": "登出成功"
}
```

---

## 用户管理接口 (Users)

### POST /api/users/register
**用户注册**

**请求体:**
```json
{
  "username": "string",
  "phone_number": "string",
  "password": "string"
}
```

**响应体 (200):**
```json
{
  "id": 1,
  "username": "string",
  "phone_number": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

**错误响应:**
- `400 Bad Request`: 用户名或手机号已存在

### GET /api/users/profile
**获取用户信息**

**响应体 (200):**
```json
{
  "id": 1,
  "username": "string",
  "phone_number": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

### PUT /api/users/profile
**更新用户信息**

**请求体:**
```json
{
  "username": "string",
  "phone_number": "string"
}
```

**响应体 (200):**
```json
{
  "id": 1,
  "username": "string",
  "phone_number": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

---

## 智能聊天接口 (Chat)


```

### POST /api/chat/completions
**聊天补全（非流式）**

**请求体:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string",
      "name": "string"
    }
  ],
  "model": "string",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**响应体 (200):**
```json
{
  "id": "string",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "string",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "string"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### POST /api/chat/completions/stream
**聊天补全（流式）**

**请求体:** 同非流式接口

**响应格式:** Server-Sent Events (SSE)
```
data: {"id": "...", "object": "...", "choices": [...]}

data: {"id": "...", "object": "...", "choices": [...]}

data: [DONE]
```

### 对话管理接口

#### GET /api/chat/conversations
**获取对话列表**

**查询参数:**
- `page`: 页码，默认1
- `page_size`: 每页数量，默认20

**响应体 (200):**
```json
{
  "conversations": [
    {
      "id": "string",
      "title": "string",
      "user_id": 1,
      "messages": [
        {
          "role": "user",
          "content": "string"
        }
      ],
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "model": "string",
      "is_active": true
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

#### POST /api/chat/conversations
**创建新对话**

**请求体:**
```json
{
  "title": "string",
  "model": "string"
}
```

**响应体 (200):**
```json
{
  "id": "string",
  "title": "string",
  "user_id": 1,
  "messages": [],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "model": "string",
  "is_active": true
}
```

#### GET /api/chat/conversations/{conversation_id}
**获取对话详情**

**响应体 (200):**
```json
{
  "id": "string",
  "title": "string",
  "user_id": 1,
  "messages": [
    {
      "role": "user",
      "content": "string"
    }
  ],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "model": "string",
  "is_active": true
}
```

#### PUT /api/chat/conversations/{conversation_id}
**更新对话信息**

**请求体:**
```json
{
  "title": "string",
  "is_active": true
}
```

**响应体 (200):** 同获取对话详情

#### DELETE /api/chat/conversations/{conversation_id}
**删除对话**

**响应体 (200):**
```json
{
  "message": "对话删除成功"
}
```

#### POST /api/chat/conversations/{conversation_id}/clear
**清空对话消息**

**响应体 (200):**
```json
{
  "message": "对话消息清空成功"
}
```

---

## 语音服务接口 (Speech)

### POST /api/speech/recognize
**语音识别**

**请求体:** FormData
- `audio_file`: 音频文件

**响应体 (200):**
```json
{
  "text": "识别出的文本",
  "confidence": 0.95
}
```

### POST /api/speech/synthesize
**语音合成**

**请求体:**
```json
{
  "text": "要合成的文本",
  "voice": "语音类型"
}
```

**响应:** 音频文件流

---

## 地图服务接口 (Map)

### GET /api/map/search
**地点搜索**

**查询参数:**
- `query`: 搜索关键词
- `location`: 位置坐标（格式：lat,lng）
- `radius`: 搜索半径（米）

**响应体 (200):**
```json
{
  "results": [
    {
      "place_id": "string",
      "name": "string",
      "address": "string",
      "location": {
        "lat": 39.9042,
        "lng": 116.4074
      }
    }
  ]
}
```

### GET /api/map/directions
**路线规划**

**查询参数:**
- `origin`: 起点
- `destination`: 终点
- `mode`: 交通方式（driving, walking, transit）

**响应体 (200):**
```json
{
  "routes": [
    {
      "distance": "10 km",
      "duration": "30 mins",
      "steps": [
        {
          "instruction": "向左转",
          "distance": "100 m",
          "duration": "1 min"
        }
      ]
    }
  ]
}
```

### GET /api/map/place/details
**地点详情**

**查询参数:**
- `place_id`: 地点ID

**响应体 (200):**
```json
{
  "place_id": "string",
  "name": "string",
  "address": "string",
  "phone": "string",
  "website": "string",
  "rating": 4.5,
  "reviews": []
}
```

---

## 旅行管理接口 (Trips)

### POST /api/trips/
**创建旅行**

**请求体:**
```json
{
  "title": "string",
  "description": "string",
  "start_date": "2024-01-01",
  "end_date": "2024-01-03",
  "destination": "string",
  "budget": 5000
}
```

**响应体 (200):**
```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "start_date": "2024-01-01",
  "end_date": "2024-01-03",
  "destination": "string",
  "budget": 5000,
  "user_id": 1,
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/trips/
**获取旅行列表**

**响应体 (200):**
```json
[
  {
    "id": 1,
    "title": "string",
    "description": "string",
    "start_date": "2024-01-01",
    "end_date": "2024-01-03",
    "destination": "string",
    "budget": 5000,
    "user_id": 1,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### GET /api/trips/{trip_id}
**获取旅行详情**

**响应体 (200):** 同创建旅行响应

### PUT /api/trips/{trip_id}
**更新旅行信息**

**请求体:** 同创建旅行请求体

**响应体 (200):** 同创建旅行响应

### DELETE /api/trips/{trip_id}
**删除旅行**

**响应体 (200):**
```json
{
  "message": "旅行删除成功"
}
```

### POST /api/trips/{trip_id}/generate
**生成旅行计划**

**响应体 (200):**
```json
{
  "message": "旅行计划生成成功",
  "plan": "生成的详细计划"
}
```

---

## 费用管理接口 (Expenses)

### POST /api/expenses/
**创建费用记录**

**请求体:**
```json
{
  "trip_id": 1,
  "category": "交通",
  "amount": 100.0,
  "description": "地铁票",
  "date": "2024-01-01"
}
```

**响应体 (200):**
```json
{
  "id": 1,
  "trip_id": 1,
  "category": "交通",
  "amount": 100.0,
  "description": "地铁票",
  "date": "2024-01-01",
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/expenses/
**获取费用列表**

**查询参数:**
- `trip_id`: 旅行ID

**响应体 (200):**
```json
[
  {
    "id": 1,
    "trip_id": 1,
    "category": "交通",
    "amount": 100.0,
    "description": "地铁票",
    "date": "2024-01-01",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### PUT /api/expenses/{expense_id}
**更新费用记录**

**请求体:** 同创建费用记录

**响应体 (200):** 同创建费用记录响应

### DELETE /api/expenses/{expense_id}
**删除费用记录**

**响应体 (200):**
```json
{
  "message": "费用记录删除成功"
}
```

### GET /api/expenses/budget/analysis
**预算分析**

**查询参数:**
- `trip_id`: 旅行ID

**响应体 (200):**
```json
{
  "total_spent": 1500.0,
  "remaining_budget": 3500.0,
  "budget_usage": 30.0,
  "category_breakdown": [
    {
      "category": "交通",
      "amount": 500.0,
      "percentage": 33.3
    }
  ]
}
```

---

## 行程详情接口 (Trip Details)

### POST /api/trip-details/
**创建行程详情**

**请求体:**
```json
{
  "trip_id": 1,
  "day": 1,
  "time": "09:00",
  "activity": "参观故宫",
  "location": "故宫",
  "description": "探索中国古代皇宫",
  "estimated_cost": 60.0
}
```

**响应体 (200):**
```json
{
  "id": 1,
  "trip_id": 1,
  "day": 1,
  "time": "09:00",
  "activity": "参观故宫",
  "location": "故宫",
  "description": "探索中国古代皇宫",
  "estimated_cost": 60.0,
  "created_at": "2024-01-01T00:00:00"
}
```

### GET /api/trip-details/
**获取行程详情列表**

**查询参数:**
- `trip_id`: 旅行ID

**响应体 (200):**
```json
[
  {
    "id": 1,
    "trip_id": 1,
    "day": 1,
    "time": "09:00",
    "activity": "参观故宫",
    "location": "故宫",
    "description": "探索中国古代皇宫",
    "estimated_cost": 60.0,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### PUT /api/trip-details/{detail_id}
**更新行程详情**

**请求体:** 同创建行程详情

**响应体 (200):** 同创建行程详情响应

### DELETE /api/trip-details/{detail_id}
**删除行程详情**

**响应体 (200):**
```json
{
  "message": "行程详情删除成功"
}
```

---

## 数据模型说明

### 用户模型 (User)
```typescript
interface User {
  id: number;
  username: string;
  phone_number: string;
  created_at: string;
}
```

### 旅行模型 (Trip)
```typescript
interface Trip {
  id: number;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  destination: string;
  budget: number;
  user_id: number;
  created_at: string;
}
```

### 费用模型 (Expense)
```typescript
interface Expense {
  id: number;
  trip_id: number;
  category: string;
  amount: number;
  description: string;
  date: string;
  created_at: string;
}
```

### 行程详情模型 (TripDetail)
```typescript
interface TripDetail {
  id: number;
  trip_id: number;
  day: number;
  time: string;
  activity: string;
  location: string;
  description: string;
  estimated_cost: number;
  created_at: string;
}
```

### 对话模型 (Conversation)
```typescript
interface Conversation {
  id: string;
  title: string;
  user_id: number;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  model: string;
  is_active: boolean;
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  name?: string;
}
```