"""
规则模型模块 (已重定向)

注意: 此模块已被重定向到src.models.db
请使用 from src.models.db import Rule 替代 from src.rule_engine.models.rule import Rule

包含规则引擎所需的所有数据模型:
- 规则类型枚举
- 规则元数据
- 规则条目
- 规则示例
- 规则模型
"""

# 导入相关类型
from pathlib import Path
from typing import Dict, List, Optional, Union

# 从新位置导入
from src.models.db import (
    Example,
    Rule,
    RuleApplication,
    RuleDependency,
    RuleItem,
    RuleMetadata,
    RuleType,
)

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = [
    "Rule",
    "RuleMetadata",
    "RuleApplication",
    "RuleDependency",
    "RuleItem",
    "Example",
    "RuleType",
]
