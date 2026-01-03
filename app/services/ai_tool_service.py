"""AI工具调用服务"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from ..models.trip import Trip
from ..schemas.ai_tool import CreateTripTool, ToolCallResult
from ..schemas.trip import Trip as TripSchema


class AiToolService:
    """AI工具调用服务类
    
    该类负责处理AI发起的工具调用请求，执行相应的操作并返回结果。
    目前支持的工具：
    - create_trip: 创建旅行行程
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化工具调用服务
        
        Args:
            db: 数据库会话对象
        """
        self.db = db
    
    async def execute_create_trip(
        self,
        tool_call_id: str,
        params: CreateTripTool,
        user_id: int
    ) -> ToolCallResult:
        """
        执行创建行程工具
        
        该方法会验证参数、创建Trip记录并保存到数据库。
        
        Args:
            tool_call_id: 工具调用ID
            params: 创建行程工具参数
            user_id: 用户ID
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、行程数据或错误信息
        
        Raises:
            ValueError: 当日期格式不正确或日期逻辑错误时抛出
        """
        try:
            # 验证日期格式
            start_date = self._parse_date(params.start_date)
            end_date = self._parse_date(params.end_date)
            
            # 验证日期逻辑（出发日期不能晚于结束日期）
            if start_date > end_date:
                return ToolCallResult(
                    tool_name="create_trip",
                    success=False,
                    error="出发日期不能晚于结束日期"
                )
            
            # 创建Trip记录
            trip = Trip(
                user_id=user_id,
                title=params.title,
                destination=params.destination,
                start_date=start_date,
                end_date=end_date,
                total_budget=params.total_budget,
                actual_expense=0.0
            )
            
            # 保存到数据库
            self.db.add(trip)
            await self.db.commit()
            await self.db.refresh(trip)
            
            # 转换为Schema格式
            trip_schema = TripSchema.model_validate(trip)
            
            # 返回成功结果
            return ToolCallResult(
                tool_name="create_trip",
                success=True,
                data={
                    "trip_id": trip.id,
                    "title": trip.title,
                    "destination": trip.destination,
                    "start_date": trip.start_date.strftime("%Y-%m-%d"),
                    "end_date": trip.end_date.strftime("%Y-%m-%d"),
                    "total_budget": trip.total_budget,
                    "created_at": trip.created_at.isoformat()
                }
            )
            
        except ValueError as e:
            # 日期格式错误
            return ToolCallResult(
                tool_name="create_trip",
                success=False,
                error=f"日期格式错误: {str(e)}"
            )
        except Exception as e:
            # 其他错误
            await self.db.rollback()
            return ToolCallResult(
                tool_name="create_trip",
                success=False,
                error=f"创建行程失败: {str(e)}"
            )
    
    async def execute_tool_call(
        self,
        tool_call_id: str,
        tool_name: str,
        arguments: str,
        user_id: int
    ) -> ToolCallResult:
        """
        执行工具调用
        
        根据工具名称路由到对应的执行方法。
        
        Args:
            tool_call_id: 工具调用ID
            tool_name: 工具名称
            arguments: 工具参数（JSON字符串）
            user_id: 用户ID
        
        Returns:
            ToolCallResult: 工具调用结果
        """
        try:
            # 根据工具名称路由到对应的执行方法
            if tool_name == "create_trip":
                # 解析参数
                params_dict = json.loads(arguments)
                params = CreateTripTool(**params_dict)
                
                # 执行创建行程
                return await self.execute_create_trip(tool_call_id, params, user_id)
            else:
                # 未知工具
                return ToolCallResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"未知的工具: {tool_name}"
                )
                
        except json.JSONDecodeError as e:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"参数解析失败: {str(e)}"
            )
        except Exception as e:
            return ToolCallResult(
                tool_name=tool_name,
                success=False,
                error=f"工具执行失败: {str(e)}"
            )
    
    @staticmethod
    def get_tool_definitions() -> list[Dict[str, Any]]:
        """
        获取工具定义列表
        
        返回所有可用工具的定义，用于传递给AI模型。
        
        Returns:
            list[Dict[str, Any]]: 工具定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_trip",
                    "description": "用于创建新的旅行行程，当用户表达想要规划旅行、去某地旅游等意图时调用",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "行程标题，如'北京5日游'"
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地，如'北京'"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "出发日期，格式：YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式：YYYY-MM-DD"
                            },
                            "total_budget": {
                                "type": "number",
                                "description": "总预算，单位：元"
                            }
                        },
                        "required": ["title", "destination", "start_date", "end_date", "total_budget"]
                    }
                }
            }
        ]
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        解析日期字符串
        
        将YYYY-MM-DD格式的字符串转换为datetime对象。
        
        Args:
            date_str: 日期字符串，格式：YYYY-MM-DD
        
        Returns:
            datetime: 解析后的日期时间对象
        
        Raises:
            ValueError: 当日期格式不正确时抛出
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"日期格式不正确，应为YYYY-MM-DD格式，实际为: {date_str}")
