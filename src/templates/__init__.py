"""
模板系统包

提供模板的定义、存储、检索和生成功能
"""

from src.templates.core.managers.template_exporter import batch_export_templates, export_template_to_file, export_template_to_markdown
from src.templates.core.template_manager import TemplateManager

__all__ = ["TemplateManager", "export_template_to_markdown", "export_template_to_file", "batch_export_templates"]
