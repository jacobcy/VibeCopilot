"""
轻量级Markdown路线图工具

这是一个轻量级的Markdown路线图工具，主要用于管理和同步项目路线图。
它支持在Markdown文件和YAML路线图之间进行转换。
"""

from .connector import GitHubConnector

# 导入转换器组件
from .converter import convert_roadmap_to_stories, convert_stories_to_roadmap
from .markdown_parser import load_sync_status, read_all_stories, save_sync_status

# 导入核心组件
from .models import Milestone, Roadmap, Task
from .roadmap_processor import RoadmapProcessor

__version__ = "0.2.0"

__all__ = [
    "Milestone",
    "Task",
    "Roadmap",
    "RoadmapProcessor",
    "GitHubConnector",
    "read_all_stories",
    "save_sync_status",
    "load_sync_status",
    "convert_roadmap_to_stories",
    "convert_stories_to_roadmap",
]
