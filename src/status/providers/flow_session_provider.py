# src/status/providers/flow_session_provider.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

# Import get_config
from src.core.config import get_config
from src.db import get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.status.core.project_state import ProjectState  # 导入 ProjectState
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class FlowSessionStatusProvider(IStatusProvider):
    """工作流会话状态提供者"""

    # 存储当前会话ID的文件路径 - 使用配置
    # CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "status", "current_session.json") # Old

    def __init__(self, project_state: ProjectState):  # 接收 ProjectState 实例
        """初始化工作流会话状态提供者

        Args:
            project_state: ProjectState 实例

        Raises:
            ValueError: 如果无法从配置中确定 current_session.json 的路径。
            OSError: 如果无法创建状态目录。
        """
        self._db_session = None
        self.project_state = project_state  # 存储 ProjectState 实例
        # 不再直接维护当前会话ID，改为使用ProjectState
        # self._current_session_id: Optional[str] = None

        # 获取配置但不再创建单独的文件
        try:
            config = get_config()
            data_dir = config.get("paths.data_dir")
            if not data_dir:
                raise ValueError("Configuration key 'paths.data_dir' is not set or invalid.")
            # 注释掉或删除，不再需要这个文件
            # self.CURRENT_SESSION_FILE = os.path.join(data_dir, "status", "current_session.json")
            # logger.debug(f"当前会话文件路径设置为: {self.CURRENT_SESSION_FILE}")
        except Exception as e:
            logger.error(f"获取配置时出错: {e}", exc_info=True)
            # Re-raise the exception to make the error visible
            raise ValueError(f"Failed to get configuration: {e}") from e

        # 不再需要创建专用目录
        # try:
        #     status_dir = os.path.dirname(self.CURRENT_SESSION_FILE)
        #     os.makedirs(status_dir, exist_ok=True)
        #     logger.debug(f"确保状态目录存在: {status_dir}")
        # except OSError as e:
        #     logger.error(f"无法创建状态目录 {status_dir}: {e}")
        #     # Re-raise the exception
        #     raise

        # 不再从文件加载，而是从ProjectState获取
        # self._load_current_session_id()

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "flow_session"

    def _get_db_session(self):
        if self._db_session is None:
            session_factory = get_session_factory()
            self._db_session = session_factory()
        return self._db_session

    # 删除这些方法，不再使用单独的文件
    # def _load_current_session_id(self) -> None:
    #     """从文件加载当前会话ID"""
    #     try:
    #         if os.path.exists(self.CURRENT_SESSION_FILE):
    #             with open(self.CURRENT_SESSION_FILE, "r") as f:
    #                 data = json.load(f)
    #                 self._current_session_id = data.get("current_session_id")
    #                 logger.debug(f"从文件加载当前会话ID: {self._current_session_id}")
    #     except Exception as e:
    #         logger.error(f"加载当前会话ID失败: {e}")

    # def _save_current_session_id(self) -> None:
    #     """保存当前会话ID到文件"""
    #     try:
    #         with open(self.CURRENT_SESSION_FILE, "w") as f:
    #             json.dump({"current_session_id": self._current_session_id}, f)
    #             logger.debug(f"保存当前会话ID到文件: {self._current_session_id}")
    #     except Exception as e:
    #         logger.error(f"保存当前会话ID失败: {e}")

    def set_current_session(self, session_id: Optional[str]) -> bool:
        """设置当前会话ID

        Args:
            session_id: 要设置为当前会话的ID, None表示清除当前会话

        Returns:
            bool: 是否成功设置
        """
        try:
            # 使用ProjectState设置当前会话ID
            # project_state = self._get_project_state() # 不再获取
            result = self.project_state.set_current_session_id(session_id)  # 直接使用存储的实例

            # 通知订阅者（如果需要）
            # TODO: 添加通知逻辑

            logger.info(f"成功设置当前会话ID: {session_id}")
            return result
        except Exception as e:
            logger.error(f"设置当前会话ID出错，session_id={session_id}: {e}", exc_info=True)
            return False

    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            Optional[str]: 当前会话ID或None
        """
        # 使用ProjectState获取当前会话ID
        # project_state = self._get_project_state() # 不再获取
        return self.project_state.get_current_session_id()  # 直接使用存储的实例

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取工作流会话状态

        Args:
            entity_id: 可选，会话ID。不提供则获取工作流会话系统整体状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            session = self._get_db_session()
            try:
                session_repo = FlowSessionRepository()

                # 获取整体状态
                if not entity_id:
                    all_sessions = session_repo.get_all(session)
                    by_status = {}
                    for flow_session in all_sessions:
                        by_status[flow_session.status] = by_status.get(flow_session.status, 0) + 1

                    # 获取当前会话信息
                    current_session_info = None
                    current_session_id = self.get_current_session_id()

                    if current_session_id:
                        current_session = session_repo.get_by_id(session, current_session_id)
                        if current_session:
                            current_session_info = {
                                "id": current_session.id,
                                "name": current_session.name,
                                "workflow_id": current_session.workflow_id,
                                "status": current_session.status,
                                "task_id": current_session.task_id,
                            }

                    return {"domain": self.domain, "total": len(all_sessions), "by_status": by_status, "current_session": current_session_info}

                # 获取特定会话状态
                flow_session = session_repo.get_by_id(session, entity_id)
                if not flow_session:
                    return {"error": f"工作流会话不存在: {entity_id}"}

                return {
                    "id": flow_session.id,
                    "name": flow_session.name,
                    "workflow_id": flow_session.workflow_id,
                    "status": flow_session.status,
                    "domain": self.domain,
                    "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                    "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
                    "task_id": flow_session.task_id,
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取工作流会话状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新工作流会话状态

        Args:
            entity_id: 会话ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            session = self._get_db_session()
            try:
                session_repo = FlowSessionRepository()
                result = session_repo.update_status(session, entity_id, status)

                if result:
                    return {"updated": True, "entity_id": entity_id, "status": status}
                else:
                    return {"updated": False, "error": "更新失败，会话可能不存在"}
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新工作流会话状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工作流会话

        Args:
            status: 可选，筛选特定状态的会话

        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        try:
            session = self._get_db_session()
            try:
                session_repo = FlowSessionRepository()
                if status:
                    sessions = session_repo.get_by_status(session, status)
                else:
                    sessions = session_repo.get_all(session)

                return [
                    {
                        "id": flow_session.id,
                        "name": flow_session.name,
                        "workflow_id": flow_session.workflow_id,
                        "status": flow_session.status,
                        "type": "flow_session",
                        "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                        "task_id": flow_session.task_id,
                    }
                    for flow_session in sessions
                ]
            finally:
                session.close()
        except Exception as e:
            logger.error(f"列出工作流会话时出错: {e}")
            return []


# 保持向后兼容的函数
def get_flow_session_status_summary() -> Dict[str, Any]:
    """
    提供工作流会话状态摘要。

    Returns:
        包含会话统计信息的字典 (total, by_status)。
    """
    provider = FlowSessionStatusProvider()
    return provider.get_status()
