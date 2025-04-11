"""
路线图YAML验证器模式

定义YAML验证器使用的各种常量和模式
"""

from typing import Dict, List

# 部分名称
SECTION_NAMES = ["metadata", "milestones", "epics", "stories", "tasks", "dependencies"]

# 有效优先级
VALID_PRIORITY = [
    "critical",
    "high",
    "medium",
    "low",
    "trivial",
    "1",
    "2",
    "3",
    "4",
    "5",
    "p0",
    "p1",
    "p2",
    "p3",
    "p4",
    "highest",
    "higher",
    "normal",
    "lower",
    "lowest",
]

# 有效状态
VALID_STATUS = [
    # 里程碑状态
    "planned",
    "in_progress",
    "completed",
    "delayed",
    "cancelled",
    # 任务状态
    "todo",
    "in_progress",
    "review",
    "done",
    "blocked",
    "on_hold",
    "completed",
    "cancelled",
    "backlog",
    "deferred",
    # 额外状态
    "not_started",
    "pending",
    "awaiting_review",
    "approved",
    "rejected",
    "merged",
    "deployed",
    "verified",
    "testing",
]

# 部分字段
SECTION_FIELDS: Dict[str, Dict[str, List[str]]] = {
    "metadata": {"required": ["title", "description"], "optional": ["version", "created_at", "updated_at", "author", "theme", "last_updated"]},
    "milestone": {"required": ["title"], "optional": ["id", "description", "start_date", "end_date", "status", "progress", "epic_ids"]},
    "epic": {"required": ["title"], "optional": ["id", "description", "status", "progress", "milestone_id", "epic_ids", "story_ids"]},
    "story": {"required": ["title"], "optional": ["id", "description", "status", "progress", "milestone_id", "epic_id", "task_ids"]},
    "task": {
        "required": ["title"],
        "optional": [
            "id",
            "description",
            "milestone_id",
            "epic_id",
            "story_id",
            "status",
            "priority",
            "assignee",
            "tags",
            "labels",
            "estimate",
            "due_date",
            "progress",
            "blocked_by",
            "depends_on",
            "effort",
            "complexity",
            "business_value",
        ],
    },
    "dependency": {"required": ["source_id", "target_id"], "optional": ["type", "description"]},
}

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

# 部分的中文名称映射
SECTION_NAMES_CH = {"milestone": "里程碑", "epic": "史诗", "story": "用户故事", "task": "任务"}


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
        "milestones": [{"title": "示例里程碑", "description": "这是一个示例里程碑", "status": "planned", "progress": 0}],
        "epics": [{"title": "示例史诗", "description": "这是一个示例史诗", "status": "planned", "progress": 0}],
        "stories": [],
        "tasks": [],
    }
