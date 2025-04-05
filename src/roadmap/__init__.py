"""
数据库模块 (已重定向)

注意: 此模块已被重定向到src.models.db（数据库模型）和src.db.repositories（仓库类）
请使用 from src.models.db import Epic, Story, Task, Label 替代 from src.roadmap.models import Epic, Story, Task, Label
"""

from src.db.repositories.roadmap_repository import RoadmapRepository

# 为保持向后兼容，从新位置导入
from src.models.db import Base, Epic, Label, Story, Task

# 创建别名以保持向后兼容
DatabaseRepository = RoadmapRepository
EpicRepository = RoadmapRepository
StoryRepository = RoadmapRepository
TaskRepository = RoadmapRepository
LabelRepository = RoadmapRepository
DbService = None  # 这个类不再支持，请使用src.db.service.DatabaseService

__all__ = [
    "Base",
    "Epic",
    "Story",
    "Task",
    "Label",
    "DatabaseRepository",
    "EpicRepository",
    "StoryRepository",
    "TaskRepository",
    "LabelRepository",
    "DbService",
]
