"""
工作流状态提供者模块

实现工作流的状态提供者接口，基于flow_session管理工作流状态。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import ensure_tables_exist, get_session_factory, init_db
from src.flow_session import FlowSessionManager, FlowStatusIntegration
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class WorkflowStatusProvider(IStatusProvider):
    """工作流状态提供者"""

    def __init__(self):
        """初始化工作流状态提供者"""
        self._db_session = None

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "workflow"

    def _get_db_session(self) -> Session:
        """获取数据库会话"""
        if self._db_session is None:
            # 确保数据库表存在
            ensure_tables_exist()

            # 获取数据库会话
            self._db_session = get_session_factory()()

        return self._db_session

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取工作流状态

        Args:
            entity_id: 可选，实体ID。格式为 "flow-<session_id>"。
                       不提供则获取整个工作流系统的状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            db_session = self._get_db_session()
            try:
                # 获取整个工作流系统状态
                if not entity_id:
                    session_manager = FlowSessionManager(db_session)
                    sessions = session_manager.list_sessions()

                    # 转换为状态系统格式
                    status_integration = FlowStatusIntegration(db_session)
                    sessions_data = []
                    for session in sessions:
                        sessions_data.append(status_integration.map_session_to_status(session))

                    return {
                        "domain": self.domain,
                        "sessions": sessions_data,
                        "count": len(sessions_data),
                    }

                # 解析实体ID
                if entity_id.startswith("flow-"):
                    session_id = entity_id[5:]  # 移除"flow-"前缀

                    # 获取会话状态
                    session_manager = FlowSessionManager(db_session)
                    session = session_manager.get_session(session_id)

                    if not session:
                        return {"error": f"找不到会话: {session_id}"}

                    # 转换为状态系统格式
                    status_integration = FlowStatusIntegration(db_session)
                    status_data = status_integration.map_session_to_status(session)
                    status_data["domain"] = self.domain

                    return status_data
                else:
                    return {"error": f"无效的实体ID格式: {entity_id}"}
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"获取工作流状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新工作流实体状态

        Args:
            entity_id: 实体ID，格式为 "flow-<session_id>"
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 验证状态值
            valid_statuses = ["IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELED"]
            if status not in valid_statuses:
                return {"error": f"无效的状态值: {status}", "updated": False}

            db_session = self._get_db_session()
            try:
                # 解析实体ID
                if not entity_id.startswith("flow-"):
                    return {"error": f"无效的实体ID格式: {entity_id}", "updated": False}

                session_id = entity_id[5:]  # 移除"flow-"前缀

                # 获取会话管理器
                session_manager = FlowSessionManager(db_session)

                # 根据状态执行对应操作
                if status == "IN_PROGRESS":
                    session_manager.resume_session(session_id)
                elif status == "ON_HOLD":
                    session_manager.pause_session(session_id)
                elif status == "COMPLETED":
                    session_manager.complete_session(session_id)
                elif status == "CANCELED":
                    session_manager.close_session(session_id)

                # 获取更新后的会话状态
                status_integration = FlowStatusIntegration(db_session)
                result = status_integration.sync_session_to_status(session_id)

                if "success" in result and result["success"]:
                    return {**result, "updated": True}
                else:
                    return {**result, "updated": False}
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"更新工作流状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工作流系统中的实体

        Args:
            status: 可选，筛选特定状态的实体

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        try:
            db_session = self._get_db_session()
            try:
                # 获取所有会话
                session_manager = FlowSessionManager(db_session)
                sessions = session_manager.list_sessions(status=status)

                # 转换为状态系统格式
                status_integration = FlowStatusIntegration(db_session)
                entities = []

                for session in sessions:
                    # 如果指定了状态筛选，转换会话状态与状态系统状态进行比较
                    session_status = status_integration.map_session_to_status(session)["status"]
                    if status and session_status != status:
                        continue

                    entities.append(
                        {
                            "id": f"flow-{session.id}",
                            "name": session.name,
                            "type": "flow_session",
                            "status": session_status,
                            "description": f"工作流: {session.workflow_id}",
                        }
                    )

                return entities
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"列出工作流实体时出错: {e}")
            return []
