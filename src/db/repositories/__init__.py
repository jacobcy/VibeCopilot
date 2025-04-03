"""
统一数据访问对象模块

从此包引入所有具体仓库类
"""

from .roadmap_repository import EpicRepository, LabelRepository, StoryRepository, TaskRepository
from .template_repository import TemplateRepository, TemplateVariableRepository

__all__ = [
    "EpicRepository",
    "StoryRepository",
    "TaskRepository",
    "LabelRepository",
    "TemplateRepository",
    "TemplateVariableRepository",
]
