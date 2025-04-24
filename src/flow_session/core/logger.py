"""
工作流会话日志管理器

提供工作流会话专用的日志记录功能。
注意：这是一个纯解释器，只负责记录工作流程，不执行任何实际操作。
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.core.log_init import get_logger


class FlowSessionLogger:
    """工作流会话日志管理器"""

    def __init__(self, session_id: str):
        """初始化日志管理器

        Args:
            session_id: 会话ID
        """
        self.session_id = session_id
        self.logger = get_logger(f"vibecopilot.flow_session.{session_id}")

    def log_session_created(self, workflow_id: str, context: Dict[str, Any]) -> None:
        """记录会话创建

        Args:
            workflow_id: 工作流ID
            context: 会话上下文
        """
        self.logger.info(
            "会话创建",
            extra={
                "event": "session_created",
                "session_id": self.session_id,
                "workflow_id": workflow_id,
                "context": context,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_session_status_changed(self, old_status: str, new_status: str, reason: Optional[str] = None) -> None:
        """记录会话状态变更

        Args:
            old_status: 原状态
            new_status: 新状态
            reason: 变更原因
        """
        self.logger.info(
            "会话状态变更",
            extra={
                "event": "session_status_changed",
                "session_id": self.session_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_session_context_updated(self, context_changes: Dict[str, Any]) -> None:
        """记录会话上下文更新

        Args:
            context_changes: 上下文变更
        """
        self.logger.info(
            "会话上下文更新",
            extra={
                "event": "session_context_updated",
                "session_id": self.session_id,
                "changes": context_changes,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_session_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录会话错误

        Args:
            error: 错误对象
            context: 错误上下文
        """
        self.logger.error(
            "会话错误",
            extra={
                "event": "session_error",
                "session_id": self.session_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_session_closed(self, reason: Optional[str] = None) -> None:
        """记录会话关闭

        Args:
            reason: 关闭原因
        """
        self.logger.info(
            "会话关闭", extra={"event": "session_closed", "session_id": self.session_id, "reason": reason, "timestamp": datetime.now().isoformat()}
        )
