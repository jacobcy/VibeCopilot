"""
规则模板模型模块

定义了表示规则模板的数据模型，包括模板元数据、变量和内容。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TemplateVariableType(str, Enum):
    """模板变量类型"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


class TemplateVariable(BaseModel):
    """模板变量定义"""

    name: str = Field(..., description="变量名称")
    type: TemplateVariableType = Field(..., description="变量类型")
    description: str = Field(..., description="变量描述")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(True, description="是否必填")
    enum_values: Optional[List[str]] = Field(None, description="枚举类型的可选值")

    @validator("enum_values")
    def validate_enum_values(cls, v, values):
        """验证枚举变量的可选值列表"""
        if values.get("type") == TemplateVariableType.ENUM and not v:
            raise ValueError("枚举类型变量必须指定可选值")
        return v


class TemplateMetadata(BaseModel):
    """模板元数据"""

    author: str = Field(..., description="作者")
    tags: List[str] = Field(default_factory=list, description="标签")
    version: str = Field("1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class Template(BaseModel):
    """规则模板模型"""

    id: Optional[str] = Field(None, description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    type: str = Field(..., description="模板类型，如agent、auto、manual等")
    variables: List[TemplateVariable] = Field(default_factory=list, description="模板变量列表")
    content: str = Field(..., description="模板内容，使用Jinja2语法")
    example: Optional[str] = Field(None, description="模板使用示例")
    metadata: TemplateMetadata = Field(default_factory=TemplateMetadata, description="元数据")

    def get_variable_by_name(self, name: str) -> Optional[TemplateVariable]:
        """通过名称获取变量"""
        for var in self.variables:
            if var.name == name:
                return var
        return None

    def validate_variable_values(self, values: Dict[str, Any]) -> Dict[str, str]:
        """验证变量值"""
        errors = {}

        # 检查所有必填变量
        for var in self.variables:
            if var.required and var.name not in values:
                errors[var.name] = f"变量 '{var.name}' 是必填的"

        # 验证提供的变量值类型
        for name, value in values.items():
            var = self.get_variable_by_name(name)
            if not var:
                errors[name] = f"未知变量 '{name}'"
                continue

            # 枚举类型检查
            if var.type == TemplateVariableType.ENUM and value not in var.enum_values:
                errors[name] = f"变量 '{name}' 的值必须是以下之一: {', '.join(var.enum_values)}"

            # 其他类型检查可以根据需要添加

        return errors

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TemplateRepository(BaseModel):
    """模板仓库信息"""

    id: str = Field(..., description="仓库ID")
    name: str = Field(..., description="仓库名称")
    description: str = Field(..., description="仓库描述")
    url: Optional[str] = Field(None, description="仓库URL")
    templates_count: int = Field(0, description="模板数量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
