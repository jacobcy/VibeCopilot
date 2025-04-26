"""
路线图验证模式定义

定义了用于验证路线图数据结构的JSON Schema
"""

from typing import Any, Dict

# 任务基本模式
TASK_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["todo", "in_progress", "done", "completed"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "assignee": {"type": "string"},
        "labels": {"type": "array", "items": {"type": "string"}},
        "estimated_hours": {"type": "number"},
        "due_date": {"type": "string", "format": "date-time"},
    },
    "additionalProperties": True,
}

# 故事基本模式
STORY_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["todo", "in_progress", "done", "completed"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "assignee": {"type": "string"},
        "tasks": {"type": "array", "items": TASK_SCHEMA},
    },
    "additionalProperties": True,
}

# 史诗基本模式
EPIC_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["todo", "in_progress", "done", "completed"]},
        "stories": {"type": "array", "items": STORY_SCHEMA},
    },
    "additionalProperties": True,
}

# 里程碑基本模式 - 用于兼容旧格式
MILESTONE_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string"},
        "tasks": {"type": "array", "items": TASK_SCHEMA},
    },
    "additionalProperties": True,
}

# 路线图元数据模式
METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": ["string", "number"]},
        "author": {"type": "string"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
    },
    "additionalProperties": True,
}

# 完整路线图模式 - 优先使用epics结构，兼容milestones结构
ROADMAP_SCHEMA = {
    "type": "object",
    "properties": {
        "metadata": METADATA_SCHEMA,
        "epics": {"type": "array", "items": EPIC_SCHEMA},
        "milestones": {"type": "array", "items": MILESTONE_SCHEMA},
        "tasks": {"type": "array", "items": TASK_SCHEMA},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": ["string", "number"]},
    },
    "additionalProperties": True,
}


def get_roadmap_schema() -> Dict[str, Any]:
    """
    获取路线图验证模式

    Returns:
        Dict[str, Any]: 路线图JSON Schema
    """
    return ROADMAP_SCHEMA
