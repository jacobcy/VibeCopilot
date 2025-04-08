"""
统一的规则模型定义

包含规则相关的所有数据模型:
- 规则元数据
- 规则条目
- 规则示例
- 规则模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .base import BaseMetadata, RuleType


class RuleMetadata(BaseMetadata):
    """规则元数据模型，扩展基础元数据"""

    dependencies: List[str] = Field(default_factory=list, description="依赖的规则ID")
    usage_count: int = Field(default=0, description="使用次数")
    effectiveness: int = Field(default=0, description="有效性评分(0-100)")


class RuleItem(BaseModel):
    """规则条目模型"""

    content: str = Field(..., description="条目内容")
    priority: int = Field(default=0, description="优先级")
    category: Optional[str] = Field(None, description="分类")


class Example(BaseModel):
    """规则示例模型"""

    content: str = Field(..., description="示例内容")
    is_valid: bool = Field(default=True, description="是否为有效示例")
    description: Optional[str] = Field(None, description="示例描述")


class Rule(BaseModel):
    """统一的规则完整模型"""

    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    type: RuleType = Field(..., description="规则类型")
    description: str = Field(..., description="规则描述")
    globs: List[str] = Field(default_factory=list, description="匹配的文件模式")
    always_apply: bool = Field(default=False, description="是否始终应用")
    items: List[RuleItem] = Field(default_factory=list, description="规则条目列表")
    examples: List[Example] = Field(default_factory=list, description="规则示例列表")
    content: str = Field(..., description="完整规则内容")
    metadata: RuleMetadata = Field(default_factory=RuleMetadata, description="元数据")

    class Config:
        """模型配置"""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class RuleApplication(BaseModel):
    """规则应用记录"""

    rule_id: str = Field(..., description="规则ID")
    applied_at: datetime = Field(default_factory=datetime.now, description="应用时间")
    file_patterns: List[str] = Field(default_factory=list, description="应用的文件模式")
    success: bool = Field(default=True, description="是否应用成功")
    feedback: Optional[Dict[str, Any]] = Field(None, description="反馈信息")


class RuleDependency(BaseModel):
    """规则依赖关系"""

    source_rule_id: str = Field(..., description="源规则ID")
    target_rule_id: str = Field(..., description="目标规则ID")
    dependency_type: str = Field("requires", description="依赖类型(requires/conflicts/enhances)")
    description: Optional[str] = Field(None, description="依赖说明")
