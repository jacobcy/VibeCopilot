"""
基础模型和共享枚举定义

包含所有模型共享的基本类型、枚举和基类
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """规则类型枚举"""

    AGENT = "agent"  # 代理选择型规则
    AUTO = "auto"  # 自动选择规则
    MANUAL = "manual"  # 手动规则
    ALWAYS = "always"  # 全局规则
    RULE = "rule"  # 通用规则，兼容现有数据


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
