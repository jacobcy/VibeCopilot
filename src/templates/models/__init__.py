"""
模板模型包 (重定向)

注意: 此包中的模型已迁移到src.models包
请使用以下导入方式替代本包导入:
- 使用 from src.models.template import Template 替代 from src.templates.models.template import Template
- 使用 from src.models.rule import Rule 替代 from src.templates.models.rule import Rule

此包内的模块仅为兼容性保留，将在未来版本中移除
"""

from src.models.rule import Rule

# 为兼容性保留，从新位置重新导出
from src.models.template import Template, TemplateMetadata, TemplateRepository, TemplateVariable

__all__ = [
    "Template",
    "TemplateVariable",
    "TemplateMetadata",
    "TemplateRepository",
    "Rule",
]
