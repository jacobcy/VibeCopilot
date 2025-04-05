"""
规则模板模型模块 (已重定向)

注意: 此模块已被重定向到src.models.db
请使用 from src.models.db import Template 替代 from src.templates.models.template import Template
"""

# 为保持向后兼容，从新位置导入
from src.models.db import (
    Template,
    TemplateMetadata,
    TemplateRepository,
    TemplateVariable,
    TemplateVariableType,
)

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = [
    "Template",
    "TemplateVariable",
    "TemplateMetadata",
    "TemplateRepository",
    "TemplateVariableType",
]
