"""
规则模型定义 (已重定向)

注意: 此模块已被重定向到src.models.rule
请使用 from src.models.rule import Rule 替代 from src.rule_engine.models.rule import Rule

包含规则引擎所需的所有数据模型:
- 规则类型枚举
- 规则元数据
- 规则条目
- 规则示例
- 规则模型
"""

from src.models.base import RuleType

# 为保持向后兼容，从新位置导入
from src.models.rule import Example, Rule, RuleApplication, RuleDependency, RuleItem, RuleMetadata

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = ["RuleType", "RuleMetadata", "RuleItem", "Example", "Rule"]
