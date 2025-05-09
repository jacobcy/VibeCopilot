# src/status/providers/task_provider.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

# Import get_config
from src.core.config import get_config
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.status.core.project_state import ProjectState  # 导入 ProjectState
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class TaskStatusProvider(IStatusProvider):
    """任务状态提供者"""

    def __init__(self, project_state: ProjectState):  # 接收 ProjectState 实例
        """初始化任务状态提供者

        Args:
            project_state: ProjectState 实例

        Raises:
            ValueError: 如果无法从配置中确定 current_task.json 的路径。
            OSError: 如果无法创建状态目录。
        """
        self._db_session = None
        self.project_state = project_state  # 存储 ProjectState 实例
        # 不再直接维护当前任务ID，改为使用ProjectState
        # self._current_task_id: Optional[str] = None

        # 不再需要维护独立的文件路径，删除相关代码
        # Get config and construct path
        try:
            config = get_config()
            data_dir = config.get("paths.data_dir")
            if not data_dir:
                raise ValueError("Configuration key 'paths.data_dir' is not set or invalid.")
            # 注释掉或删除，不再需要这个文件
            # self.CURRENT_TASK_FILE = os.path.join(data_dir, "status", "current_task.json")
            # logger.debug(f"当前任务文件路径设置为: {self.CURRENT_TASK_FILE}")
        except Exception as e:
            logger.error(f"获取配置时出错: {e}", exc_info=True)
            # Re-raise the exception to make the error visible
            raise ValueError(f"Failed to get configuration: {e}") from e

        # 不再需要创建目录
        # 确保status目录存在
        # try:
        #     status_dir = os.path.dirname(self.CURRENT_TASK_FILE)
        #     os.makedirs(status_dir, exist_ok=True)
        #     logger.debug(f"确保状态目录存在: {status_dir}")
        # except OSError as e:
        #     logger.error(f"无法创建状态目录 {status_dir}: {e}")
        #     # Re-raise the exception
        #     raise

        # 不再从文件加载，而是从ProjectState获取
        # self._load_current_task_id()

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "task"

    def _get_db_session(self):
        if self._db_session is None:
            session_factory = get_session_factory()
            self._db_session = session_factory()
        return self._db_session

    # 删除这些方法，不再使用单独的文件
    # def _load_current_task_id(self) -> None:
    #     """从文件加载当前任务ID"""
    #     try:
    #         if os.path.exists(self.CURRENT_TASK_FILE):
    #             with open(self.CURRENT_TASK_FILE, "r") as f:
    #                 data = json.load(f)
    #                 self._current_task_id = data.get("current_task_id")
    #                 logger.debug(f"从文件加载当前任务ID: {self._current_task_id}")
    #     except Exception as e:
    #         logger.error(f"加载当前任务ID失败: {e}")

    # def _save_current_task_id(self) -> None:
    #     """保存当前任务ID到文件"""
    #     try:
    #         with open(self.CURRENT_TASK_FILE, "w") as f:
    #             json.dump({"current_task_id": self._current_task_id}, f)
    #             logger.debug(f"保存当前任务ID到文件: {self._current_task_id}")
    #     except Exception as e:
    #         logger.error(f"保存当前任务ID失败: {e}")
    #         logger.warning("Failed to save current task ID to file.")

    def set_current_task(self, task_id: Optional[str]) -> bool:
        """设置当前任务ID

        Args:
            task_id: 要设置为当前任务的ID, None表示清除当前任务

        Returns:
            bool: 是否成功设置
        """
        try:
            logger.debug(f"尝试设置当前任务ID: {task_id}")

            # 使用ProjectState设置当前任务ID
            # project_state = self._get_project_state() # 不再获取
            result = self.project_state.set_current_task_id(task_id)  # 直接使用存储的实例

            # 通知订阅者（如果需要）
            # TODO: 添加通知逻辑

            logger.info(f"成功设置当前任务ID: {task_id}")
            return result
        except Exception as e:
            # Log detailed exception info
            logger.error(f"设置当前任务ID出错，task_id={task_id}: {e}", exc_info=True)
            return False

    def get_current_task_id(self) -> Optional[str]:
        """获取当前任务ID

        Returns:
            Optional[str]: 当前任务ID或None
        """
        # 使用ProjectState获取当前任务ID
        # project_state = self._get_project_state() # 不再获取
        return self.project_state.get_current_task_id()  # 直接使用存储的实例

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务状态

        Args:
            entity_id: 可选，任务ID。不提供则获取任务系统整体状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository()

                # 获取整体状态
                if not entity_id:
                    all_tasks = task_repo.get_all(session)
                    by_status = {}
                    for task in all_tasks:
                        by_status[task.status] = by_status.get(task.status, 0) + 1

                    # 获取当前任务信息
                    current_task_info = None
                    current_task_id = self.get_current_task_id()

                    if current_task_id:
                        current_task = task_repo.get_by_id(session, current_task_id)
                        if current_task:
                            current_task_info = {
                                "id": current_task.id,
                                "title": current_task.title,
                                "status": current_task.status,
                                "priority": current_task.priority,
                                "assignee": current_task.assignee,
                            }

                    return {"domain": self.domain, "total": len(all_tasks), "by_status": by_status, "current_task": current_task_info}

                # 获取特定任务状态
                task = task_repo.get_by_id(session, entity_id)
                if not task:
                    return {"error": f"任务不存在: {entity_id}"}

                return {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "domain": self.domain,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取任务状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新任务状态

        Args:
            entity_id: 任务ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository()
                result = task_repo.update_status(session, entity_id, status)

                if result:
                    return {"updated": True, "entity_id": entity_id, "status": status}
                else:
                    return {"updated": False, "error": "更新失败，任务可能不存在"}
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新任务状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出任务

        Args:
            status: 可选，筛选特定状态的任务

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository()
                tasks = task_repo.get_all(session, status=status)

                return [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "type": "task",
                        "created_at": task.created_at,
                    }
                    for task in tasks
                ]
            finally:
                session.close()
        except Exception as e:
            logger.error(f"列出任务时出错: {e}")
            return []


# 保持向后兼容的函数
def get_task_status_summary() -> Dict[str, Any]:
    """
    提供 Task 状态摘要。

    Returns:
        包含任务统计信息的字典 (total, by_status)。
    """
    provider = TaskStatusProvider()
    return provider.get_status()
