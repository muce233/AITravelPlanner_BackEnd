"""AI工具调用服务"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from ..models.trip import Trip
from ..models.conversation import Conversation
from ..schemas.ai_tool import ToolCallResult


class AiToolService:
    """AI工具调用服务类
    
    该类负责处理AI发起的工具调用请求，执行相应的操作并返回结果。
    目前支持的工具：
    - read_trip: 读取旅行行程
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化工具调用服务
        
        Args:
            db: 数据库会话对象
        """
        self.db = db
    
    async def execute_read_trip(
        self,
        tool_call_id: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行读取行程工具
        
        该方法会根据对话ID读取关联的Trip记录并返回详细信息。
        
        Args:
            tool_call_id: 工具调用ID
            params: 读取行程工具参数（不需要参数）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、行程数据或错误信息
        """
        try:
            # 检查是否提供了conversation_id
            if not conversation_id:
                return ToolCallResult(
                    tool_name="read_trip",
                    success=False,
                    error="当前对话没有关联的行程，无法读取"
                )
            
            # 从对话关联的行程获取trip_id
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            # 如果对话没有关联的行程
            if not trip_id:
                return ToolCallResult(
                    tool_name="read_trip",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            # 根据trip_id查询行程
            stmt = select(Trip).where(
                Trip.id == trip_id,
                Trip.user_id == user_id
            )
            result = await self.db.execute(stmt)
            trip = result.scalar_one_or_none()
            
            # 如果行程不存在
            if not trip:
                return ToolCallResult(
                    tool_name="read_trip",
                    success=False,
                    error="行程不存在或无权限访问"
                )
            
            # 查询关联的conversation
            conv_stmt = select(Conversation.id).where(Conversation.trip_id == trip.id)
            conv_result = await self.db.execute(conv_stmt)
            conversation_id_result = conv_result.scalar_one_or_none()
            
            # 返回成功结果
            return ToolCallResult(
                tool_name="read_trip",
                success=True,
                data={
                    "trip_id": str(trip.id),
                    "title": trip.title,
                    "destination": trip.destination,
                    "start_date": trip.start_date.strftime("%Y-%m-%d") if trip.start_date else None,
                    "end_date": trip.end_date.strftime("%Y-%m-%d") if trip.end_date else None,
                    # "total_budget": trip.total_budget,
                    # "actual_expense": trip.actual_expense,
                    "conversation_id": conversation_id_result,
                    "created_at": trip.created_at.isoformat(),
                    "updated_at": trip.updated_at.isoformat() if trip.updated_at else None
                }
            )
            
        except Exception as e:
            # 其他错误
            return ToolCallResult(
                tool_name="read_trip",
                success=False,
                error=f"读取行程失败: {str(e)}"
            )
    
    async def execute_edit_trip(
        self,
        tool_call_id: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行编辑行程工具
        
        该方法会根据对话ID获取关联的行程，然后根据提供的参数更新行程信息。
        支持更新的字段包括：title、destination、start_date、end_date
        
        Args:
            tool_call_id: 工具调用ID
            arguments: 编辑行程工具参数（JSON字符串）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、更新后的行程数据或错误信息
        """
        try:
            # 检查是否提供了conversation_id
            if not conversation_id:
                return ToolCallResult(
                    tool_name="edit_trip",
                    success=False,
                    error="当前对话没有关联的行程，无法编辑"
                )
            
            # 解析参数
            try:
                params = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolCallResult(
                    tool_name="edit_trip",
                    success=False,
                    error="参数格式错误，请提供有效的JSON格式参数"
                )
            
            # 从对话关联的行程获取trip_id
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            # 如果对话没有关联的行程
            if not trip_id:
                return ToolCallResult(
                    tool_name="edit_trip",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            # 根据trip_id查询行程
            stmt = select(Trip).where(
                Trip.id == trip_id,
                Trip.user_id == user_id
            )
            result = await self.db.execute(stmt)
            trip = result.scalar_one_or_none()
            
            # 如果行程不存在
            if not trip:
                return ToolCallResult(
                    tool_name="edit_trip",
                    success=False,
                    error="行程不存在或无权限访问"
                )
            
            # 检查是否有需要更新的字段
            update_fields = []
            if "title" in params and params["title"] is not None:
                trip.title = params["title"]
                update_fields.append("标题")
            
            if "destination" in params and params["destination"] is not None:
                trip.destination = params["destination"]
                update_fields.append("目的地")
            
            if "start_date" in params and params["start_date"] is not None:
                try:
                    trip.start_date = datetime.fromisoformat(params["start_date"])
                    update_fields.append("开始日期")
                except ValueError:
                    return ToolCallResult(
                        tool_name="edit_trip",
                        success=False,
                        error="开始日期格式错误，请使用YYYY-MM-DD格式"
                    )
            
            if "end_date" in params and params["end_date"] is not None:
                try:
                    trip.end_date = datetime.fromisoformat(params["end_date"])
                    update_fields.append("结束日期")
                except ValueError:
                    return ToolCallResult(
                        tool_name="edit_trip",
                        success=False,
                        error="结束日期格式错误，请使用YYYY-MM-DD格式"
                    )
            
            # 如果没有需要更新的字段
            if not update_fields:
                return ToolCallResult(
                    tool_name="edit_trip",
                    success=False,
                    error="没有提供需要更新的字段。支持更新的字段包括：title、destination、start_date、end_date"
                )
            
            # 提交更改
            await self.db.commit()
            await self.db.refresh(trip)
            
            # 查询关联的conversation
            conv_stmt = select(Conversation.id).where(Conversation.trip_id == trip.id)
            conv_result = await self.db.execute(conv_stmt)
            conversation_id_result = conv_result.scalar_one_or_none()
            
            # 返回成功结果
            return ToolCallResult(
                tool_name="edit_trip",
                success=True,
                data={
                    "trip_id": str(trip.id),
                    "title": trip.title,
                    "destination": trip.destination,
                    "start_date": trip.start_date.strftime("%Y-%m-%d") if trip.start_date else None,
                    "end_date": trip.end_date.strftime("%Y-%m-%d") if trip.end_date else None,
                    "conversation_id": conversation_id_result,
                    "updated_fields": update_fields,
                    "created_at": trip.created_at.isoformat(),
                    "updated_at": trip.updated_at.isoformat() if trip.updated_at else None
                }
            )
            
        except Exception as e:
            # 其他错误
            return ToolCallResult(
                tool_name="edit_trip",
                success=False,
                error=f"编辑行程失败: {str(e)}"
            )
    
    async def execute_tool_call(
        self,
        tool_call_id: str,
        tool_name: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行工具调用
        
        根据工具名称路由到对应的执行方法。
        
        Args:
            tool_call_id: 工具调用ID
            tool_name: 工具名称
            arguments: 工具参数（JSON字符串）
            user_id: 用户ID
            conversation_id: 对话ID（可选，用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果
        """
        try:
            # 根据工具名称路由到对应的执行方法
            if tool_name == "read_trip":
                # 执行读取行程
                return await self.execute_read_trip(tool_call_id, user_id, conversation_id)
            elif tool_name == "edit_trip":
                # 执行编辑行程
                return await self.execute_edit_trip(tool_call_id, arguments, user_id, conversation_id)
            else:
                # 未知工具
                return ToolCallResult(
                    tool_name=tool_name,
                    success=False,
                    error=f"未知的工具: {tool_name}"
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
                    "name": "read_trip",
                    "description": "用于读取当前对话关联的旅行行程信息，当用户询问行程的详细信息时调用。该工具会自动使用当前对话关联的行程，不需要用户提供任何参数。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_trip",
                    "description": "用于编辑当前对话关联的旅行行程信息。该工具会先读取当前行程，然后根据用户提供的参数更新指定的字段。支持更新的字段包括：title（标题）、destination（目的地）、start_date（开始日期，格式YYYY-MM-DD）、end_date（结束日期，格式YYYY-MM-DD）。该工具会自动使用当前对话关联的行程。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "行程标题"
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式为YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式为YYYY-MM-DD"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
