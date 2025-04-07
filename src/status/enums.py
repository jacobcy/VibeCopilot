"""
状态枚举模块

定义系统中使用的各种状态枚举和转换规则。
"""

from enum import Enum, auto
from typing import Dict, List, Set


class StatusCategory(Enum):
    """状态类别枚举"""

    TODO = auto()  # 待办/计划中
    IN_PROGRESS = auto()  # 进行中
    COMPLETED = auto()  # 已完成
    BLOCKED = auto()  # 被阻塞
    CANCELLED = auto()  # 已取消


class RoadmapElementStatus:
    """路线图元素状态枚举"""

    # 里程碑状态
    MILESTONE_PLANNED = "planned"  # 计划中
    MILESTONE_IN_PROGRESS = "in_progress"  # 进行中
    MILESTONE_COMPLETED = "completed"  # 已完成
    MILESTONE_CANCELLED = "cancelled"  # 已取消

    # 任务状态
    TASK_TODO = "todo"  # 待办
    TASK_IN_PROGRESS = "in_progress"  # 进行中
    TASK_COMPLETED = "completed"  # 已完成
    TASK_BLOCKED = "blocked"  # 被阻塞
    TASK_CANCELLED = "cancelled"  # 已取消

    # 状态映射到类别
    STATUS_CATEGORY_MAP = {
        MILESTONE_PLANNED: StatusCategory.TODO,
        MILESTONE_IN_PROGRESS: StatusCategory.IN_PROGRESS,
        MILESTONE_COMPLETED: StatusCategory.COMPLETED,
        MILESTONE_CANCELLED: StatusCategory.CANCELLED,
        TASK_TODO: StatusCategory.TODO,
        TASK_IN_PROGRESS: StatusCategory.IN_PROGRESS,
        TASK_COMPLETED: StatusCategory.COMPLETED,
        TASK_BLOCKED: StatusCategory.BLOCKED,
        TASK_CANCELLED: StatusCategory.CANCELLED,
    }

    # 有效的状态转换
    VALID_TRANSITIONS = {
        MILESTONE_PLANNED: {MILESTONE_IN_PROGRESS, MILESTONE_CANCELLED},
        MILESTONE_IN_PROGRESS: {MILESTONE_COMPLETED, MILESTONE_CANCELLED},
        MILESTONE_COMPLETED: {MILESTONE_IN_PROGRESS},
        MILESTONE_CANCELLED: {MILESTONE_PLANNED},
        TASK_TODO: {TASK_IN_PROGRESS, TASK_CANCELLED},
        TASK_IN_PROGRESS: {TASK_COMPLETED, TASK_BLOCKED, TASK_CANCELLED},
        TASK_COMPLETED: {TASK_IN_PROGRESS},
        TASK_BLOCKED: {TASK_IN_PROGRESS, TASK_CANCELLED},
        TASK_CANCELLED: {TASK_TODO},
    }

    @classmethod
    def is_valid_transition(cls, current_status: str, new_status: str) -> bool:
        """检查状态转换是否有效

        Args:
            current_status: 当前状态
            new_status: 新状态

        Returns:
            bool: 转换是否有效
        """
        if current_status == new_status:  # 允许相同状态
            return True

        if current_status not in cls.VALID_TRANSITIONS:
            return False

        return new_status in cls.VALID_TRANSITIONS[current_status]

    @classmethod
    def get_category(cls, status: str) -> StatusCategory:
        """获取状态对应的类别

        Args:
            status: 状态值

        Returns:
            StatusCategory: 状态类别
        """
        return cls.STATUS_CATEGORY_MAP.get(status, StatusCategory.TODO)


class WorkflowStatus:
    """工作流状态枚举"""

    # 工作流状态
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

    # 执行状态
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    # 状态映射到类别
    STATUS_CATEGORY_MAP = {
        ACTIVE: StatusCategory.IN_PROGRESS,
        INACTIVE: StatusCategory.TODO,
        ARCHIVED: StatusCategory.COMPLETED,
        PENDING: StatusCategory.TODO,
        RUNNING: StatusCategory.IN_PROGRESS,
        COMPLETED: StatusCategory.COMPLETED,
        FAILED: StatusCategory.BLOCKED,
        CANCELLED: StatusCategory.CANCELLED,
    }

    # 有效的状态转换
    VALID_TRANSITIONS = {
        ACTIVE: {INACTIVE, ARCHIVED},
        INACTIVE: {ACTIVE, ARCHIVED},
        ARCHIVED: {INACTIVE},
        PENDING: {RUNNING, CANCELLED},
        RUNNING: {COMPLETED, FAILED, CANCELLED},
        COMPLETED: set(),  # 终态
        FAILED: {PENDING},
        CANCELLED: {PENDING},
    }

    @classmethod
    def is_valid_transition(cls, current_status: str, new_status: str) -> bool:
        """检查状态转换是否有效"""
        if current_status == new_status:
            return True

        if current_status not in cls.VALID_TRANSITIONS:
            return False

        return new_status in cls.VALID_TRANSITIONS[current_status]

    @classmethod
    def get_category(cls, status: str) -> StatusCategory:
        """获取状态对应的类别"""
        return cls.STATUS_CATEGORY_MAP.get(status, StatusCategory.TODO)
