"""
规则引擎模型模块 (已重定向)

注意: 此模块已被重定向到src.models
请使用 from src.models.rule import Rule 替代 from src.rule_engine.models.rule import Rule
"""

# 为保持向后兼容，从新位置导入
from src.models.base import RuleType, TemplateVariableType
from src.models.rule import Example, Rule, RuleItem, RuleMetadata
from src.models.template import Template, TemplateMetadata, TemplateVariable

__all__ = [
    "Rule",
    "RuleType",
    "RuleItem",
    "RuleMetadata",
    "Example",
    "Template",
    "TemplateVariable",
    "TemplateMetadata",
    "TemplateVariableType",
]
