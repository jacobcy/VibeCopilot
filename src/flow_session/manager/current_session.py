"""
工作流当前会话管理

提供工作流当前会话的设置、获取和切换功能。
"""

import json
import os
from typing import Optional

from src.models.db import FlowSession


class CurrentSessionMixin:
    """当前会话管理混入类"""

    def switch_session(self, id_or_name: str) -> FlowSession:
        """切换到指定会话 (设置为当前会话)

        Args:
            id_or_name: 会话ID或名称

        Returns:
            切换后的会话对象

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 设置为当前会话
        self._set_current_session(session.id)

        # 将会话标记为当前会话
        session.is_current = True
        self.session_repo.update(session.id, {"is_current": True})

        # 清除其他会话的is_current标志
        other_sessions = self.session.query(FlowSession).filter(FlowSession.id != session.id).all()
        for other in other_sessions:
            if other.is_current:
                other.is_current = False
                self.session_repo.update(other.id, {"is_current": False})

        # 自动关联任务 - 禁用此功能以避免循环引用
        # 原先的代码会导致循环引用问题:
        # FlowSessionManager.switch_session -> TaskService -> TaskSessionService.set_current_task
        # -> FlowSessionManager.switch_session -> ...
        #
        # if session.task_id:
        #    try:
        #        # 使用导入的TaskService来保持松耦合
        #        from src.services.task import TaskService
        #
        #        task_service = TaskService()
        #        task_service.set_current_task(session.task_id)
        #    except Exception as e:
        #        self._log("log_session_error", f"自动切换任务失败: {e}")

        self._log("log_session_switched", session.id, session.name)
        return session

    def get_current_session(self) -> Optional[FlowSession]:
        """获取当前会话

        Returns:
            当前会话对象或None
        """
        session_id = self._get_current_session_id()
        if not session_id:
            return None

        return self.get_session(session_id)

    def _set_current_session(self, session_id: str) -> None:
        """设置当前会话ID（内部方法）

        使用文件和数据库双重记录当前会话ID，保证会话跟踪的可靠性。

        Args:
            session_id: 会话ID
        """
        # 在文件中记录当前会话ID
        try:
            with open(self.CURRENT_SESSION_FILE, "w") as f:
                json.dump({"current_session_id": session_id}, f)
        except Exception as e:
            self._log("log_session_error", f"保存当前会话ID到文件失败: {e}")

        # 同时在数据库中设置当前会话
        try:
            self.session_repo.set_current_session(session_id)
        except Exception as e:
            self._log("log_session_error", f"设置数据库当前会话状态失败: {e}")

        # 记录日志
        self._log("log_current_session_set", session_id)

    def _get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            当前会话ID或None
        """
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                with open(self.CURRENT_SESSION_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("current_session_id")
        except Exception as e:
            self._log("log_error", f"获取当前会话ID失败: {str(e)}")
        return None

    def _clear_current_session(self) -> None:
        """清除当前会话设置"""
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                os.remove(self.CURRENT_SESSION_FILE)
        except Exception as e:
            self._log("log_error", f"清除当前会话设置失败: {str(e)}")
