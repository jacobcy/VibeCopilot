"""规则模板模型定义 (已重定向)

注意: 模板相关模型已移至src.models.db目录
请使用以下导入替代:
- from src.models.db import Template, TemplateVariable, TemplateMetadata
- from src.models.db import Rule, RuleMetadata
- from src.models.db import RuleType, TemplateVariableType
"""

# 重定向导入
from src.models.db import (
    BaseMetadata,
    Rule,
    RuleApplication,
    RuleDependency,
    RuleMetadata,
    RuleType,
    Template,
    TemplateMetadata,
    TemplateRepository,
    TemplateVariable,
    TemplateVariableType,
)

__all__ = [
    "Template",
    "TemplateVariable",
    "TemplateMetadata",
    "TemplateRepository",
    "Rule",
    "RuleMetadata",
    "RuleApplication",
    "RuleDependency",
    "RuleType",
    "TemplateVariableType",
    "BaseMetadata",
]
