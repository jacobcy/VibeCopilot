"""
路线图数据模型

定义路线图相关的数据库模型。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Roadmap:
    """路线图"""

    id: str
    name: str
    description: Optional[str] = None
    is_active: bool = False
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Epic:
    """史诗"""

    id: str
    name: str
    roadmap_id: str  # 关联的路线图ID
    description: Optional[str] = None
    status: str = "planned"  # planned, in_progress, completed
    progress: int = 0
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Milestone:
    """里程碑"""

    id: str
    name: str
    roadmap_id: str  # 关联的路线图ID
    description: Optional[str] = None
    status: str = "planned"  # planned, in_progress, completed
    progress: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    epic_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Story:
    """用户故事"""

    id: str
    title: str
    roadmap_id: str  # 关联的路线图ID
    description: Optional[str] = None
    status: str = "planned"  # planned, in_progress, completed
    progress: int = 0
    milestone_id: Optional[str] = None
    epic_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Task:
    """任务"""

    id: str
    title: str
    roadmap_id: str  # 关联的路线图ID
    description: Optional[str] = None
    status: str = "todo"  # todo, in_progress, completed
    priority: str = "P2"  # P0, P1, P2, P3
    milestone: Optional[str] = None
    story_id: Optional[str] = None
    epic: Optional[str] = None
    assignee: Optional[str] = None
    estimate: int = 8  # 估计工时
    labels: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
