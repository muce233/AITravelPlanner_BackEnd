"""AI工具调用服务"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from ..models.trip import Trip
from ..models.trip_detail import TripDetail
from ..models.conversation import Conversation
from ..schemas.ai_tool import ToolCallResult


class AiToolService:
    """AI工具调用服务类
    
    该类负责处理AI发起的工具调用请求，执行相应的操作并返回结果。
    目前支持的工具：
    - read_trip: 读取旅行行程
    - edit_trip: 编辑旅行行程
    - create_trip_detail: 创建行程点
    - read_trip_details: 读取行程点列表
    - update_trip_detail: 更新行程点
    - delete_trip_detail: 删除行程点
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
    
    async def execute_create_trip_detail(
        self,
        tool_call_id: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行创建行程点工具
        
        该方法会根据对话ID获取关联的行程，然后创建一个新的行程点。
        
        Args:
            tool_call_id: 工具调用ID
            arguments: 创建行程点工具参数（JSON字符串）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、创建的行程点数据或错误信息
        """
        try:
            if not conversation_id:
                return ToolCallResult(
                    tool_name="create_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程，无法创建行程点"
                )
            
            try:
                params = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolCallResult(
                    tool_name="create_trip_detail",
                    success=False,
                    error="参数格式错误，请提供有效的JSON格式参数"
                )
            
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            if not trip_id:
                return ToolCallResult(
                    tool_name="create_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            stmt = select(Trip).where(
                Trip.id == trip_id,
                Trip.user_id == user_id
            )
            result = await self.db.execute(stmt)
            trip = result.scalar_one_or_none()
            
            if not trip:
                return ToolCallResult(
                    tool_name="create_trip_detail",
                    success=False,
                    error="行程不存在或无权限访问"
                )
            
            day = params.get("day")
            type_value = params.get("type")
            name = params.get("name")
            
            if not day or not type_value or not name:
                return ToolCallResult(
                    tool_name="create_trip_detail",
                    success=False,
                    error="缺少必要参数：day（第几天）、type（类型：景点/住宿/餐厅/交通）、name（名称）为必填项"
                )
            
            location = params.get("location")
            address = params.get("address")
            start_time_str = params.get("start_time")
            end_time_str = params.get("end_time")
            description = params.get("description")
            price = params.get("price", 0.0)
            notes = params.get("notes")
            images = params.get("images")
            
            start_time = None
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                except ValueError:
                    return ToolCallResult(
                        tool_name="create_trip_detail",
                        success=False,
                        error="开始时间格式错误，请使用ISO格式"
                    )
            
            end_time = None
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str)
                except ValueError:
                    return ToolCallResult(
                        tool_name="create_trip_detail",
                        success=False,
                        error="结束时间格式错误，请使用ISO格式"
                    )
            
            new_detail = TripDetail(
                trip_id=trip_id,
                day=day,
                type=type_value,
                name=name,
                location=location,
                address=address,
                start_time=start_time,
                end_time=end_time,
                description=description,
                price=price,
                notes=notes,
                images=images
            )
            
            self.db.add(new_detail)
            await self.db.commit()
            await self.db.refresh(new_detail)
            
            return ToolCallResult(
                tool_name="create_trip_detail",
                success=True,
                data={
                    "detail_id": str(new_detail.id),
                    "day": new_detail.day,
                    "type": new_detail.type,
                    "name": new_detail.name,
                    "location": new_detail.location,
                    "address": new_detail.address,
                    "start_time": new_detail.start_time.isoformat() if new_detail.start_time else None,
                    "end_time": new_detail.end_time.isoformat() if new_detail.end_time else None,
                    "description": new_detail.description,
                    "price": new_detail.price,
                    "notes": new_detail.notes,
                    "images": new_detail.images
                }
            )
            
        except Exception as e:
            return ToolCallResult(
                tool_name="create_trip_detail",
                success=False,
                error=f"创建行程点失败: {str(e)}"
            )
    
    async def execute_read_trip_details(
        self,
        tool_call_id: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行读取行程点列表工具
        
        该方法会根据对话ID获取关联的行程，然后读取该行程的所有行程点。
        
        Args:
            tool_call_id: 工具调用ID
            arguments: 读取行程点工具参数（JSON字符串，可选参数day用于筛选特定天）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、行程点列表或错误信息
        """
        try:
            if not conversation_id:
                return ToolCallResult(
                    tool_name="read_trip_details",
                    success=False,
                    error="当前对话没有关联的行程，无法读取行程点"
                )
            
            try:
                params = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolCallResult(
                    tool_name="read_trip_details",
                    success=False,
                    error="参数格式错误，请提供有效的JSON格式参数"
                )
            
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            if not trip_id:
                return ToolCallResult(
                    tool_name="read_trip_details",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            stmt = select(Trip).where(
                Trip.id == trip_id,
                Trip.user_id == user_id
            )
            result = await self.db.execute(stmt)
            trip = result.scalar_one_or_none()
            
            if not trip:
                return ToolCallResult(
                    tool_name="read_trip_details",
                    success=False,
                    error="行程不存在或无权限访问"
                )
            
            day_filter = params.get("day")
            
            if day_filter is not None:
                stmt = select(TripDetail).where(
                    TripDetail.trip_id == trip_id,
                    TripDetail.day == day_filter
                )
            else:
                stmt = select(TripDetail).where(TripDetail.trip_id == trip_id)
            
            stmt = stmt.order_by(TripDetail.day, TripDetail.start_time)
            result = await self.db.execute(stmt)
            details = result.scalars().all()
            
            details_list = []
            for detail in details:
                details_list.append({
                    "detail_id": str(detail.id),
                    "day": detail.day,
                    "type": detail.type,
                    "name": detail.name,
                    "location": detail.location,
                    "address": detail.address,
                    "start_time": detail.start_time.isoformat() if detail.start_time else None,
                    "end_time": detail.end_time.isoformat() if detail.end_time else None,
                    "description": detail.description,
                    "price": detail.price,
                    "notes": detail.notes,
                    "images": detail.images
                })
            
            return ToolCallResult(
                tool_name="read_trip_details",
                success=True,
                data={
                    "trip_id": str(trip.id),
                    "total_count": len(details_list),
                    "details": details_list
                }
            )
            
        except Exception as e:
            return ToolCallResult(
                tool_name="read_trip_details",
                success=False,
                error=f"读取行程点失败: {str(e)}"
            )
    
    async def execute_update_trip_detail(
        self,
        tool_call_id: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行更新行程点工具
        
        该方法会根据行程点ID更新指定的行程点信息。
        
        Args:
            tool_call_id: 工具调用ID
            arguments: 更新行程点工具参数（JSON字符串，必须包含detail_id）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态、更新后的行程点数据或错误信息
        """
        try:
            if not conversation_id:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程，无法更新行程点"
                )
            
            try:
                params = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="参数格式错误，请提供有效的JSON格式参数"
                )
            
            detail_id = params.get("detail_id")
            
            if not detail_id:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="缺少必要参数：detail_id（行程点ID）为必填项"
                )
            
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            if not trip_id:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            stmt = select(TripDetail).where(
                TripDetail.id == detail_id,
                TripDetail.trip_id == trip_id
            )
            result = await self.db.execute(stmt)
            detail = result.scalar_one_or_none()
            
            if not detail:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="行程点不存在或无权限访问"
                )
            
            update_fields = []
            
            if "day" in params and params["day"] is not None:
                detail.day = params["day"]
                update_fields.append("第几天")
            
            if "type" in params and params["type"] is not None:
                detail.type = params["type"]
                update_fields.append("类型")
            
            if "name" in params and params["name"] is not None:
                detail.name = params["name"]
                update_fields.append("名称")
            
            if "location" in params:
                detail.location = params["location"]
                update_fields.append("位置")
            
            if "address" in params:
                detail.address = params["address"]
                update_fields.append("地址")
            
            if "start_time" in params:
                if params["start_time"] is not None:
                    try:
                        detail.start_time = datetime.fromisoformat(params["start_time"])
                        update_fields.append("开始时间")
                    except ValueError:
                        return ToolCallResult(
                            tool_name="update_trip_detail",
                            success=False,
                            error="开始时间格式错误，请使用ISO格式"
                        )
                else:
                    detail.start_time = None
                    update_fields.append("开始时间")
            
            if "end_time" in params:
                if params["end_time"] is not None:
                    try:
                        detail.end_time = datetime.fromisoformat(params["end_time"])
                        update_fields.append("结束时间")
                    except ValueError:
                        return ToolCallResult(
                            tool_name="update_trip_detail",
                            success=False,
                            error="结束时间格式错误，请使用ISO格式"
                        )
                else:
                    detail.end_time = None
                    update_fields.append("结束时间")
            
            if "description" in params:
                detail.description = params["description"]
                update_fields.append("描述")
            
            if "price" in params:
                detail.price = params["price"]
                update_fields.append("价格")
            
            if "notes" in params:
                detail.notes = params["notes"]
                update_fields.append("备注")
            
            if "images" in params:
                detail.images = params["images"]
                update_fields.append("图片")
            
            if not update_fields:
                return ToolCallResult(
                    tool_name="update_trip_detail",
                    success=False,
                    error="没有提供需要更新的字段"
                )
            
            await self.db.commit()
            await self.db.refresh(detail)
            
            return ToolCallResult(
                tool_name="update_trip_detail",
                success=True,
                data={
                    "detail_id": str(detail.id),
                    "day": detail.day,
                    "type": detail.type,
                    "name": detail.name,
                    "location": detail.location,
                    "address": detail.address,
                    "start_time": detail.start_time.isoformat() if detail.start_time else None,
                    "end_time": detail.end_time.isoformat() if detail.end_time else None,
                    "description": detail.description,
                    "price": detail.price,
                    "notes": detail.notes,
                    "images": detail.images,
                    "updated_fields": update_fields
                }
            )
            
        except Exception as e:
            return ToolCallResult(
                tool_name="update_trip_detail",
                success=False,
                error=f"更新行程点失败: {str(e)}"
            )
    
    async def execute_delete_trip_detail(
        self,
        tool_call_id: str,
        arguments: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        执行删除行程点工具
        
        该方法会根据行程点ID删除指定的行程点。
        
        Args:
            tool_call_id: 工具调用ID
            arguments: 删除行程点工具参数（JSON字符串，必须包含detail_id）
            user_id: 用户ID
            conversation_id: 对话ID（用于获取对话关联的行程）
        
        Returns:
            ToolCallResult: 工具调用结果，包含成功状态或错误信息
        """
        try:
            if not conversation_id:
                return ToolCallResult(
                    tool_name="delete_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程，无法删除行程点"
                )
            
            try:
                params = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                return ToolCallResult(
                    tool_name="delete_trip_detail",
                    success=False,
                    error="参数格式错误，请提供有效的JSON格式参数"
                )
            
            detail_id = params.get("detail_id")
            
            if not detail_id:
                return ToolCallResult(
                    tool_name="delete_trip_detail",
                    success=False,
                    error="缺少必要参数：detail_id（行程点ID）为必填项"
                )
            
            conv_stmt = select(Conversation.trip_id).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conv_result = await self.db.execute(conv_stmt)
            trip_id = conv_result.scalar_one_or_none()
            
            if not trip_id:
                return ToolCallResult(
                    tool_name="delete_trip_detail",
                    success=False,
                    error="当前对话没有关联的行程"
                )
            
            stmt = select(TripDetail).where(
                TripDetail.id == detail_id,
                TripDetail.trip_id == trip_id
            )
            result = await self.db.execute(stmt)
            detail = result.scalar_one_or_none()
            
            if not detail:
                return ToolCallResult(
                    tool_name="delete_trip_detail",
                    success=False,
                    error="行程点不存在或无权限访问"
                )
            
            detail_name = detail.name
            await self.db.delete(detail)
            await self.db.commit()
            
            return ToolCallResult(
                tool_name="delete_trip_detail",
                success=True,
                data={
                    "detail_id": str(detail_id),
                    "deleted_detail_name": detail_name,
                    "message": "行程点删除成功"
                }
            )
            
        except Exception as e:
            return ToolCallResult(
                tool_name="delete_trip_detail",
                success=False,
                error=f"删除行程点失败: {str(e)}"
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
            if tool_name == "read_trip":
                return await self.execute_read_trip(tool_call_id, user_id, conversation_id)
            elif tool_name == "edit_trip":
                return await self.execute_edit_trip(tool_call_id, arguments, user_id, conversation_id)
            elif tool_name == "create_trip_detail":
                return await self.execute_create_trip_detail(tool_call_id, arguments, user_id, conversation_id)
            elif tool_name == "read_trip_details":
                return await self.execute_read_trip_details(tool_call_id, arguments, user_id, conversation_id)
            elif tool_name == "update_trip_detail":
                return await self.execute_update_trip_detail(tool_call_id, arguments, user_id, conversation_id)
            elif tool_name == "delete_trip_detail":
                return await self.execute_delete_trip_detail(tool_call_id, arguments, user_id, conversation_id)
            else:
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
            },
            {
                "type": "function",
                "function": {
                    "name": "create_trip_detail",
                    "description": "用于创建新的行程点。该工具会在当前对话关联的行程中添加一个新的行程点。必填参数包括：day（第几天）、type（类型：景点/住宿/餐厅/交通）、name（名称）。可选参数包括：location（位置，经纬度对象）、address（地址）、start_time（开始时间，ISO格式）、end_time（结束时间，ISO格式）、description（描述）、price（价格）、notes（备注）、images（图片链接数组）。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "day": {
                                "type": "integer",
                                "description": "第几天"
                            },
                            "type": {
                                "type": "string",
                                "description": "类型，可选值：景点、住宿、餐厅、交通",
                                "enum": ["景点", "住宿", "餐厅", "交通"]
                            },
                            "name": {
                                "type": "string",
                                "description": "行程点名称"
                            },
                            "location": {
                                "type": "object",
                                "description": "位置信息，包含经纬度",
                                "properties": {
                                    "lat": {
                                        "type": "number",
                                        "description": "纬度"
                                    },
                                    "lng": {
                                        "type": "number",
                                        "description": "经度"
                                    }
                                }
                            },
                            "address": {
                                "type": "string",
                                "description": "详细地址"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "开始时间，ISO格式，例如：2024-01-01T09:00:00"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "结束时间，ISO格式，例如：2024-01-01T11:00:00"
                            },
                            "description": {
                                "type": "string",
                                "description": "行程点描述"
                            },
                            "price": {
                                "type": "number",
                                "description": "价格"
                            },
                            "notes": {
                                "type": "string",
                                "description": "备注信息"
                            },
                            "images": {
                                "type": "array",
                                "description": "图片链接数组",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["day", "type", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_trip_details",
                    "description": "用于读取当前对话关联的行程的所有行程点。该工具会返回行程中的所有行程点列表，可以按天筛选。可选参数：day（第几天），如果不提供则返回所有天的行程点。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "day": {
                                "type": "integer",
                                "description": "筛选特定天的行程点，如果不提供则返回所有天的行程点"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_trip_detail",
                    "description": "用于更新指定的行程点信息。该工具会根据行程点ID更新对应的行程点。必填参数：detail_id（行程点ID）。可选参数：day（第几天）、type（类型）、name（名称）、location（位置）、address（地址）、start_time（开始时间，ISO格式）、end_time（结束时间，ISO格式）、description（描述）、price（价格）、notes（备注）、images（图片链接数组）。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "detail_id": {
                                "type": "string",
                                "description": "行程点ID"
                            },
                            "day": {
                                "type": "integer",
                                "description": "第几天"
                            },
                            "type": {
                                "type": "string",
                                "description": "类型，可选值：景点、住宿、餐厅、交通",
                                "enum": ["景点", "住宿", "餐厅", "交通"]
                            },
                            "name": {
                                "type": "string",
                                "description": "行程点名称"
                            },
                            "location": {
                                "type": "object",
                                "description": "位置信息，包含经纬度",
                                "properties": {
                                    "lat": {
                                        "type": "number",
                                        "description": "纬度"
                                    },
                                    "lng": {
                                        "type": "number",
                                        "description": "经度"
                                    }
                                }
                            },
                            "address": {
                                "type": "string",
                                "description": "详细地址"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "开始时间，ISO格式，例如：2024-01-01T09:00:00"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "结束时间，ISO格式，例如：2024-01-01T11:00:00"
                            },
                            "description": {
                                "type": "string",
                                "description": "行程点描述"
                            },
                            "price": {
                                "type": "number",
                                "description": "价格"
                            },
                            "notes": {
                                "type": "string",
                                "description": "备注信息"
                            },
                            "images": {
                                "type": "array",
                                "description": "图片链接数组",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["detail_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_trip_detail",
                    "description": "用于删除指定的行程点。该工具会根据行程点ID删除对应的行程点。必填参数：detail_id（行程点ID）。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "detail_id": {
                                "type": "string",
                                "description": "要删除的行程点ID"
                            }
                        },
                        "required": ["detail_id"]
                    }
                }
            }
        ]
