"""
模板模型定义 (已重定向)

注意: 此模块已被重定向到src.models.template
请使用 from src.models.template import Template 替代 from src.rule_engine.models.template import Template

包含规则模板相关的所有数据模型:
- 模板变量
- 模板元数据
- 模板模型
"""

from src.models.base import TemplateVariableType

# 为保持向后兼容，从新位置导入
from src.models.template import Template, TemplateMetadata, TemplateRepository, TemplateVariable

# 仅导出旧版本支持的类，防止代码崩溃
__all__ = ["TemplateVariable", "TemplateMetadata", "Template"]
