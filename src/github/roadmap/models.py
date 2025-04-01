"""
路线图数据模型

定义路线图相关的数据结构，包括里程碑和任务。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Milestone:
    """里程碑数据模型"""

    id: str
    name: str
    description: str
    start_date: str
    end_date: str
    status: str
    progress: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Milestone":
        """从字典创建里程碑对象"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            status=data.get("status", "planned"),
            progress=data.get("progress", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "progress": self.progress,
        }


@dataclass
class Task:
    """任务数据模型"""

    id: str
    title: str
    description: str
    milestone: str
    status: str
    priority: str
    assignees: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建任务对象"""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            milestone=data.get("milestone", ""),
            status=data.get("status", "todo"),
            priority=data.get("priority", "P2"),
            assignees=data.get("assignees", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "milestone": self.milestone,
            "status": self.status,
            "priority": self.priority,
            "assignees": self.assignees,
        }


@dataclass
class Roadmap:
    """路线图数据模型"""

    title: str
    description: str
    last_updated: str
    milestones: List[Milestone] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Roadmap":
        """从字典创建路线图对象"""
        milestones = [Milestone.from_dict(m) for m in data.get("milestones", [])]
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            last_updated=data.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
            milestones=milestones,
            tasks=tasks,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "description": self.description,
            "last_updated": self.last_updated,
            "milestones": [m.to_dict() for m in self.milestones],
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def get_milestone_by_id(self, milestone_id: str) -> Optional[Milestone]:
        """根据ID获取里程碑"""
        for milestone in self.milestones:
            if milestone.id == milestone_id:
                return milestone
        return None

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_milestone(self, milestone_id: str) -> List[Task]:
        """获取指定里程碑的所有任务"""
        return [task for task in self.tasks if task.milestone == milestone_id]

    def get_active_milestone(self) -> Optional[Milestone]:
        """获取当前活跃的里程碑"""
        for milestone in self.milestones:
            if milestone.status == "in_progress":
                return milestone
        return None

    def update_milestone_progress(self, milestone_id: str) -> None:
        """更新里程碑进度"""
        milestone = self.get_milestone_by_id(milestone_id)
        if not milestone:
            return

        tasks = self.get_tasks_by_milestone(milestone_id)
        if not tasks:
            return

        completed_tasks = [t for t in tasks if t.status == "completed"]
        progress = int(len(completed_tasks) / len(tasks) * 100) if tasks else 0
        milestone.progress = progress
