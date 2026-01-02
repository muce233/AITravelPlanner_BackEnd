from pydantic import BaseModel, Field
from enum import StrEnum


class PromptTemplateType(StrEnum):
    """提示词模板类型枚举"""
    新增行程


class PromptTemplate(BaseModel):
    """提示词模板模型
    
    用于表示一个提示词模板,包含模板的基本信息和内容。
    
    Attributes:
        template_type: 模板类型,使用PromptTemplateType枚举值
        template_content: 模板内容,可以包含占位符用于后续格式化
    """
    template_type: PromptTemplateType = Field(..., description="模板类型")
    template_content: str = Field(..., description="模板内容")
