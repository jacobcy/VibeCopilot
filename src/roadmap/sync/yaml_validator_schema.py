"""
路线图YAML验证器模式定义模块

包含路线图YAML文件的字段定义、状态枚举值和其他常量
"""

from typing import Dict, List

# 定义路线图模型字段
ROADMAP_FIELDS = {
    "required": ["title", "description"],
    "optional": ["version", "author", "theme", "last_updated"],
}

MILESTONE_FIELDS = {
    "required": ["title", "description"],
    "optional": ["status", "progress", "start_date", "end_date", "epic"],
}

EPIC_FIELDS = {"required": ["title", "description"], "optional": ["status", "progress"]}

STORY_FIELDS = {
    "required": ["title", "description"],
    "optional": ["status", "progress", "milestone", "epic"],
}

TASK_FIELDS = {
    "required": ["title", "description"],
    "optional": [
        "status",
        "priority",
        "milestone",
        "epic",
        "story",
        "assignee",
        "estimate",
        "labels",
    ],
}

# 定义状态枚举值
VALID_STATUS = {
    "milestone": ["planned", "in_progress", "completed"],
    "epic": ["planned", "in_progress", "completed"],
    "story": ["planned", "in_progress", "completed"],
    "task": ["todo", "in_progress", "completed"],
}

# 定义优先级枚举值
VALID_PRIORITY = ["P0", "P1", "P2", "P3"]

# 部分的中文名称映射
SECTION_NAMES = {"milestone": "里程碑", "epic": "史诗", "story": "用户故事", "task": "任务"}


# 默认模板数据结构
def get_default_template_data() -> Dict:
    """
    获取默认模板数据

    Returns:
        Dict: 默认模板数据结构
    """
    from datetime import datetime

    return {
        "title": "示例路线图",
        "description": "这是一个示例路线图",
        "version": "1.0",
        "author": "VibeCopilot",
        "theme": "",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "milestones": [
            {"title": "示例里程碑", "description": "这是一个示例里程碑", "status": "planned", "progress": 0}
        ],
        "epics": [{"title": "示例史诗", "description": "这是一个示例史诗", "status": "planned", "progress": 0}],
        "stories": [],
        "tasks": [],
    }
