"""
工作流阶段日志管理器

提供工作流阶段专用的日志记录功能。
注意：这是一个纯解释器，只负责记录工作流阶段的状态变化，不执行任何实际操作。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from src.core.log_init import get_logger


class StageLogger:
    """工作流阶段日志管理器"""

    def __init__(self, session_id: str, stage_id: str):
        """初始化日志管理器

        Args:
            session_id: 会话ID
            stage_id: 阶段ID
        """
        self.session_id = session_id
        self.stage_id = stage_id
        self.logger = get_logger(f"flow_session.{session_id}.stage.{stage_id}", is_workflow=True)

    def log_stage_created(self, stage_type: str, context: Dict[str, Any]) -> None:
        """记录阶段创建

        Args:
            stage_type: 阶段类型
            context: 阶段上下文
        """
        self.logger.info(
            "阶段创建",
            extra={
                "event": "stage_created",
                "session_id": self.session_id,
                "stage_id": self.stage_id,
                "stage_type": stage_type,
                "context": context,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_stage_status_changed(self, old_status: str, new_status: str, reason: Optional[str] = None) -> None:
        """记录阶段状态变更

        Args:
            old_status: 原状态
            new_status: 新状态
            reason: 变更原因
        """
        self.logger.info(
            "阶段状态变更",
            extra={
                "event": "stage_status_changed",
                "session_id": self.session_id,
                "stage_id": self.stage_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_stage_context_updated(self, context_changes: Dict[str, Any]) -> None:
        """记录阶段上下文更新

        Args:
            context_changes: 上下文变更
        """
        self.logger.info(
            "阶段上下文更新",
            extra={
                "event": "stage_context_updated",
                "session_id": self.session_id,
                "stage_id": self.stage_id,
                "changes": context_changes,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_stage_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录阶段错误

        Args:
            error: 错误对象
            context: 错误上下文
        """
        self.logger.error(
            "阶段错误",
            extra={
                "event": "stage_error",
                "session_id": self.session_id,
                "stage_id": self.stage_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_stage_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        """记录阶段完成

        Args:
            result: 完成结果
        """
        self.logger.info(
            "阶段完成",
            extra={
                "event": "stage_completed",
                "session_id": self.session_id,
                "stage_id": self.stage_id,
                "result": result or {},
                "timestamp": datetime.now().isoformat(),
            },
        )
