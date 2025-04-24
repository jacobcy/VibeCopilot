"""
工作流当前会话管理

提供工作流当前会话的设置、获取和切换功能。
"""

import json
import logging
import os
from typing import Optional

from src.models.db import FlowSession

logger = logging.getLogger(__name__)


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

        # 设置为当前会话，使用新的Provider模式
        self._set_current_session(session.id)

        # 恢复并修改任务联动逻辑 - 使用新的Provider模式
        if session.task_id:
            try:
                # 使用状态服务和Provider
                from src.status.service import StatusService

                status_service = StatusService.get_instance()
                task_provider = status_service.provider_manager.get_provider("task")

                if task_provider and hasattr(task_provider, "set_current_task"):
                    task_provider.set_current_task(session.task_id)
                    logger.info(f"已将任务 {session.task_id} 设置为当前任务")
            except Exception as e:
                self._log("log_session_error", f"自动切换任务失败: {e}")

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

        现在只使用Provider模式，不再直接更新数据库。

        Args:
            session_id: 会话ID
        """
        try:
            # 使用状态服务和Provider
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            session_provider = status_service.provider_manager.get_provider("flow_session")

            if session_provider and hasattr(session_provider, "set_current_session"):
                session_provider.set_current_session(session_id)
                logger.info(f"已将会话 {session_id} 设置为当前会话")
            else:
                # 作为备份，继续使用文件存储
                self._save_current_session_to_file(session_id)
        except Exception as e:
            # 出错时，使用文件存储作为备份
            self._save_current_session_to_file(session_id)
            self._log("log_session_error", f"使用Provider设置当前会话失败: {e}")

        # 记录日志
        self._log("log_current_session_set", session_id)

    def _save_current_session_to_file(self, session_id: str) -> None:
        """保存当前会话ID到文件（备用方法）"""
        try:
            with open(self.CURRENT_SESSION_FILE, "w") as f:
                json.dump({"current_session_id": session_id}, f)
        except Exception as e:
            self._log("log_session_error", f"保存当前会话ID到文件失败: {e}")

    def _get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        优先使用Provider，如果失败则回退到文件存储。

        Returns:
            当前会话ID或None
        """
        try:
            # 优先使用Provider
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            session_provider = status_service.provider_manager.get_provider("flow_session")

            if session_provider and hasattr(session_provider, "get_current_session_id"):
                session_id = session_provider.get_current_session_id()
                if session_id:
                    return session_id

            # 回退到文件存储
            return self._get_current_session_id_from_file()
        except Exception as e:
            self._log("log_error", f"获取当前会话ID失败: {e}")
            # 出错时回退到文件存储
            return self._get_current_session_id_from_file()

    def _get_current_session_id_from_file(self) -> Optional[str]:
        """从文件获取当前会话ID（备用方法）"""
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                with open(self.CURRENT_SESSION_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("current_session_id")
        except Exception as e:
            self._log("log_error", f"从文件获取当前会话ID失败: {e}")
        return None

    def _clear_current_session(self) -> None:
        """清除当前会话设置"""
        try:
            # 使用Provider
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            session_provider = status_service.provider_manager.get_provider("flow_session")

            if session_provider and hasattr(session_provider, "set_current_session"):
                session_provider.set_current_session(None)

            # 同时清除文件存储
            if os.path.exists(self.CURRENT_SESSION_FILE):
                os.remove(self.CURRENT_SESSION_FILE)
        except Exception as e:
            self._log("log_error", f"清除当前会话设置失败: {e}")

    def _log(self, log_type, *args):
        """记录日志"""
        if hasattr(self, "_logger") and self._logger:
            if log_type == "log_session_switched":
                session_id, session_name = args
                self._logger.info(f"已切换到会话: {session_name} ({session_id})")
            elif log_type == "log_current_session_set":
                session_id = args[0]
                self._logger.info(f"已设置当前会话ID: {session_id}")
            elif log_type == "log_session_error":
                error = args[0]
                self._logger.error(f"会话操作出错: {error}")
            elif log_type == "log_error":
                error = args[0]
                self._logger.error(f"错误: {error}")
        else:
            # 如果没有设置logger，使用标准logger
            if log_type.startswith("log_error") or log_type.startswith("log_session_error"):
                logger.error(f"{args}")
            else:
                logger.info(f"{args}")
