"""
路线图数据模型

定义路线图相关的数据库模型。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# 创建基础类，单个实例用于所有模型
Base = declarative_base()


@dataclass
class Roadmap:
    """路线图"""

    id: str
    name: str
    description: Optional[str] = None
    status: str = "active"  # active, archived
    owner: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Epic:
    """史诗"""

    id: str
    title: str
    roadmap_id: str
    description: str = ""
    status: str = "draft"  # draft, in_progress, completed
    tasks: List[str] = field(default_factory=list)
    milestone: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Milestone:
    """里程碑"""

    id: str
    title: str
    roadmap_id: str
    description: str = ""
    status: str = "planned"  # planned, in_progress, completed
    due_date: Optional[datetime] = None
    tasks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Story:
    """用户故事"""

    id: str
    title: str
    roadmap_id: str
    description: str = ""
    epic_id: str = ""
    status: str = "draft"  # draft, in_progress, completed
    tasks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Task类改为SQLAlchemy模型
class Task(Base):
    """任务"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    roadmap_id = Column(String, nullable=True, index=True)
    description = Column(String, default="")
    status = Column(String, default="todo")  # todo, in_progress, completed
    priority = Column(String, default="P2")  # P0, P1, P2, P3
    milestone = Column(String, default="")
    story_id = Column(String, nullable=True)
    epic = Column(String, default="")
    assignee = Column(String, default="")
    estimate = Column(Integer, default=0)  # 估计工时，单位小时
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(
        self,
        id: str,
        title: str,
        roadmap_id: Optional[str] = None,
        description: str = "",
        status: str = "todo",
        priority: str = "P2",
        milestone: str = "",
        story_id: Optional[str] = None,
        epic: str = "",
        assignee: str = "",
        estimate: int = 0,
        **kwargs,
    ):
        self.id = id
        self.title = title
        self.roadmap_id = roadmap_id
        self.description = description
        self.status = status
        self.priority = priority
        self.milestone = milestone
        self.story_id = story_id
        self.epic = epic
        self.assignee = assignee
        self.estimate = estimate

        # 使用当前时间初始化时间戳
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示

        Returns:
            字典表示
        """
        return {
            "id": self.id,
            "title": self.title,
            "roadmap_id": self.roadmap_id,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "milestone": self.milestone,
            "story_id": self.story_id,
            "epic": self.epic,
            "assignee": self.assignee,
            "estimate": self.estimate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
