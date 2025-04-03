"""
规则模型模块

定义了表示规则的数据模型。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """规则类型"""

    AGENT = "agent"
    AUTO = "auto"
    MANUAL = "manual"
    ALWAYS = "always"


class RuleMetadata(BaseModel):
    """规则元数据"""

    author: str = Field(..., description="作者")
    tags: List[str] = Field(default_factory=list, description="标签")
    version: str = Field("1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    dependencies: List[str] = Field(default_factory=list, description="依赖的规则ID")
    usage_count: int = Field(0, description="使用次数")
    effectiveness: int = Field(0, description="有效性评分(0-100)")


class Rule(BaseModel):
    """规则模型"""

    id: Optional[str] = Field(None, description="规则ID")
    name: str = Field(..., description="规则名称")
    type: RuleType = Field(..., description="规则类型")
    description: str = Field(..., description="规则描述")
    globs: List[str] = Field(default_factory=list, description="匹配的文件模式")
    always_apply: bool = Field(False, description="是否始终应用")
    content: str = Field(..., description="规则内容")
    metadata: RuleMetadata = Field(default_factory=RuleMetadata, description="元数据")

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class RuleApplication(BaseModel):
    """规则应用记录"""

    rule_id: str = Field(..., description="规则ID")
    applied_at: datetime = Field(default_factory=datetime.now, description="应用时间")
    file_patterns: List[str] = Field(default_factory=list, description="应用的文件模式")
    success: bool = Field(True, description="是否应用成功")
    feedback: Optional[Dict[str, Any]] = Field(None, description="反馈信息")


class RuleDependency(BaseModel):
    """规则依赖关系"""

    source_rule_id: str = Field(..., description="源规则ID")
    target_rule_id: str = Field(..., description="目标规则ID")
    dependency_type: str = Field("requires", description="依赖类型(requires/conflicts/enhances)")
    description: Optional[str] = Field(None, description="依赖说明")
