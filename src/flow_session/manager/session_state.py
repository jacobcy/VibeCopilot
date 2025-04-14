"""
工作流会话状态管理

提供工作流会话的状态管理功能，如完成和关闭会话。
"""

from typing import Any, Dict, Optional

from src.models.db import FlowSession


class SessionStateMixin:
    """会话状态管理混入类"""

    def update_session_status(self, id_or_name: str, new_status: str, reason: Optional[str] = None) -> Optional[FlowSession]:
        """更新会话状态

        Args:
            id_or_name: 会话ID或名称
            new_status: 新状态
            reason: 状态变更原因

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        old_status = session.status
        updated_session = self.session_repo.update_status(session.id, new_status)

        if updated_session:
            self._log("log_session_status_changed", old_status, new_status, reason)

        return updated_session

    def start_session(self, id_or_name: str) -> Optional[FlowSession]:
        """启动会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            启动的会话对象或None

        Raises:
            ValueError: 如果会话状态不允许启动
        """
        session = self.get_session(id_or_name)
        if not session:
            return None

        if session.status not in ["PENDING", "CREATED"]:
            raise ValueError(f"无法启动状态为 {session.status} 的会话")

        # 更新会话状态
        session.status = "ACTIVE"
        self.session_repo.update(session.id, {"status": "ACTIVE"})

        # 记录会话启动
        self._log("log_session_started", session.id, session.name)

        return session

    def complete_session(self, id_or_name: str) -> Optional[FlowSession]:
        """完成会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果会话状态不允许完成
        """
        session = self.get_session(id_or_name)
        if not session:
            return None

        if session.status in ["COMPLETED", "CLOSED", "ERROR"]:
            raise ValueError(f"无法完成状态为 {session.status} 的会话")

        # 更新会话状态
        session.status = "COMPLETED"
        self.session_repo.update(session.id, {"status": "COMPLETED"})

        # 记录会话完成
        self._log("log_session_completed", session.id, session.name)

        return session

    def close_session(self, id_or_name: str, reason: Optional[str] = None) -> Optional[FlowSession]:
        """结束会话

        结束会话意味着该会话已经达到了最终状态，不再进行任何操作。
        与完成不同，关闭可以应用于任何状态的会话，表示放弃继续处理。

        Args:
            id_or_name: 会话ID或名称
            reason: 关闭原因

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            return None

        # 会话可以从任何状态关闭
        session.status = "CLOSED"
        self.session_repo.update(session.id, {"status": "CLOSED"})

        # 记录会话关闭和原因
        context = {"reason": reason} if reason else {}
        self._log("log_session_closed", session.id, session.name, context)

        return session
