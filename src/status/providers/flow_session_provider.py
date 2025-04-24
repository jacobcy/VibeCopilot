# src/status/providers/flow_session_provider.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.db import get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class FlowSessionStatusProvider(IStatusProvider):
    """工作流会话状态提供者"""

    # 存储当前会话ID的文件路径
    CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "status", "current_session.json")

    def __init__(self):
        """初始化工作流会话状态提供者"""
        self._db_session = None
        self._current_session_id: Optional[str] = None

        # 确保status目录存在
        os.makedirs(os.path.dirname(self.CURRENT_SESSION_FILE), exist_ok=True)

        # 从持久化存储加载当前会话ID
        self._load_current_session_id()

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "flow_session"

    def _get_db_session(self):
        if self._db_session is None:
            session_factory = get_session_factory()
            self._db_session = session_factory()
        return self._db_session

    def _load_current_session_id(self) -> None:
        """从文件加载当前会话ID"""
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                with open(self.CURRENT_SESSION_FILE, "r") as f:
                    data = json.load(f)
                    self._current_session_id = data.get("current_session_id")
                    logger.debug(f"从文件加载当前会话ID: {self._current_session_id}")
        except Exception as e:
            logger.error(f"加载当前会话ID失败: {e}")

    def _save_current_session_id(self) -> None:
        """保存当前会话ID到文件"""
        try:
            with open(self.CURRENT_SESSION_FILE, "w") as f:
                json.dump({"current_session_id": self._current_session_id}, f)
                logger.debug(f"保存当前会话ID到文件: {self._current_session_id}")
        except Exception as e:
            logger.error(f"保存当前会话ID失败: {e}")

    def set_current_session(self, session_id: Optional[str]) -> bool:
        """设置当前会话ID

        Args:
            session_id: 要设置为当前会话的ID, None表示清除当前会话

        Returns:
            bool: 是否成功设置
        """
        try:
            # 设置当前会话ID
            self._current_session_id = session_id

            # 保存到文件
            self._save_current_session_id()

            # 通知订阅者（如果需要）
            # TODO: 添加通知逻辑

            logger.info(f"成功设置当前会话ID: {session_id}")
            return True
        except Exception as e:
            logger.error(f"设置当前会话ID失败: {e}")
            return False

    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            Optional[str]: 当前会话ID或None
        """
        return self._current_session_id

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
