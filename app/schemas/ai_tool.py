"""AI工具调用相关数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class ToolDefinition(BaseModel):
    """工具定义模型
    
    用于定义AI可以调用的工具，包含工具的名称、描述和参数schema。
    
    Attributes:
        type: 工具类型，固定为"function"
        function: 函数定义，包含name、description和parameters
    """
    type: Literal["function"] = Field(default="function", description="工具类型")
    function: Dict[str, Any] = Field(..., description="函数定义，包含name、description和parameters")


class ToolCall(BaseModel):
    """工具调用模型
    
    表示AI发起的工具调用请求。
    
    Attributes:
        id: 工具调用ID，用于标识这次工具调用
        type: 调用类型，固定为"function"
        function: 函数调用信息，包含name和arguments
    """
    id: str = Field(..., description="工具调用ID")
    type: Literal["function"] = Field(default="function", description="调用类型")
    function: Dict[str, str] = Field(..., description="函数调用信息，包含name和arguments")


class CreateTripTool(BaseModel):
    """创建行程工具参数模型
    
    用于创建行程时提取的参数。
    
    Attributes:
        title: 行程标题，如"北京5日游"
        destination: 目的地，如"北京"
        start_date: 出发日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        total_budget: 总预算，单位：元
    """
    title: str = Field(..., description="行程标题，如'北京5日游'")
    destination: str = Field(..., description="目的地，如'北京'")
    start_date: str = Field(..., description="出发日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    total_budget: float = Field(..., description="总预算，单位：元")


class ToolCallResult(BaseModel):
    """工具调用结果模型
    
    表示工具执行后的结果。
    
    Attributes:
        tool_name: 工具名称
        success: 是否执行成功
        data: 执行成功时返回的数据
        error: 执行失败时的错误信息
    """
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="是否执行成功")
    data: Optional[Dict[str, Any]] = Field(None, description="执行成功时返回的数据")
    error: Optional[str] = Field(None, description="执行失败时的错误信息")


class ToolMessage(BaseModel):
    """工具消息模型
    
    用于在对话历史中记录工具调用的消息。
    
    Attributes:
        role: 消息角色，固定为"tool"
        tool_call_id: 工具调用ID
        content: 工具执行结果
    """
    role: Literal["tool"] = Field(default="tool", description="消息角色")
    tool_call_id: str = Field(..., description="工具调用ID")
    content: str = Field(..., description="工具执行结果")
