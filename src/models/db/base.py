"""
数据库模型基类

提供所有数据库模型的公共基类和功能
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.declarative import declarative_base

# 创建SQLAlchemy基类
Base = declarative_base()


# 自定义Base.to_dict方法
def _to_dict(self):
    """安全地将模型实例转换为字典，只包含直接属性而不包含关系"""
    result = {}
    for column in self.__table__.columns:
        column_name = column.name
        attr_value = getattr(self, column_name, None)
        result[column_name] = attr_value
    return result


# 添加方法到Base类
Base.to_dict = _to_dict


class RuleType(str, Enum):
    """规则类型枚举"""

    AGENT = "agent"  # 代理选择型规则
    AUTO = "auto"  # 自动选择规则
    MANUAL = "manual"  # 手动规则
    ALWAYS = "always"  # 全局规则


class TemplateVariableType(str, Enum):
    """模板变量类型"""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


class BaseMetadata(BaseModel):
    """基础元数据模型"""

    author: str = Field(default="VibeCopilot")
    tags: List[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}
