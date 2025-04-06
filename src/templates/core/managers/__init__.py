"""
模板管理器模块

提供模板的管理、查询和操作功能的分离模块
"""

from src.templates.core.managers.template_loader import TemplateLoader
from src.templates.core.managers.template_searcher import TemplateSearcher
from src.templates.core.managers.template_updater import TemplateUpdater

__all__ = ["TemplateLoader", "TemplateSearcher", "TemplateUpdater"]
