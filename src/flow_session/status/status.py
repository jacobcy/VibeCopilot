"""
工作流状态定义模块

定义工作流会话和阶段的状态。
"""

from enum import Enum, auto


class StageStatus(str, Enum):
    """工作流阶段状态"""

    PENDING = "PENDING"  # 待处理
    ACTIVE = "ACTIVE"  # 执行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 执行失败
    PAUSED = "PAUSED"  # 已暂停


class SessionStatus(str, Enum):
    """工作流会话状态"""

    PENDING = "PENDING"  # 待处理
    ACTIVE = "ACTIVE"  # 执行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 执行失败
    PAUSED = "PAUSED"  # 已暂停
