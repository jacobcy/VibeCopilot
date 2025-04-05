"""
规则模型模块 (已重定向)

注意: 此模块已被重定向到src.models.db
请使用 from src.models.db import Rule 替代 from src.templates.models.rule import Rule
"""

# 为保持向后兼容，从新位置导入
from src.models.db import Rule, RuleApplication, RuleDependency, RuleMetadata, RuleType

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = ["Rule", "RuleMetadata", "RuleType", "RuleApplication", "RuleDependency"]
