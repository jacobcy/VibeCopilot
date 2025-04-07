"""
状态订阅服务

实现IStatusSubscriber接口，订阅系统状态变更并同步到外部系统
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.status.interfaces import IStatusSubscriber

logger = logging.getLogger(__name__)


class StatusSyncSubscriber(IStatusSubscriber):
    """状态同步订阅者

    订阅状态变更事件，将状态同步到外部系统（如n8n）
    """

    def __init__(self, db_session: Session):
        """初始化状态同步订阅者

        Args:
            db_session: 数据库会话
        """
        self.db_session = db_session
        logger.info("状态同步订阅者已初始化")

    def on_status_changed(
        self,
        domain: str,
        entity_id: str,
        old_status: str,
        new_status: str,
        context: Dict[str, Any],
    ) -> None:
        """状态变更事件处理

        当系统中的状态发生变更时，此方法会被调用，用于同步状态到外部系统

        Args:
            domain: 领域名称（如 'roadmap', 'workflow'）
            entity_id: 实体ID
            old_status: 旧状态
            new_status: 新状态
            context: 上下文信息，包含额外的状态数据
        """
        logger.info(f"状态变更: {domain}/{entity_id}: {old_status} -> {new_status}")

        try:
            # 根据领域类型处理不同的状态同步
            if domain == "workflow":
                self._sync_workflow_status(entity_id, new_status, context)
            elif domain == "roadmap":
                self._sync_roadmap_status(entity_id, new_status, context)
            else:
                logger.debug(f"不支持的领域类型: {domain}")
        except Exception as e:
            logger.exception(f"同步状态时发生错误: {e}")

    def _sync_workflow_status(self, workflow_id: str, status: str, context: Dict[str, Any]) -> None:
        """同步工作流状态

        Args:
            workflow_id: 工作流ID
            status: 新状态
            context: 上下文信息
        """
        try:
            # 导入WorkflowSync服务
            from adapters.n8n.adapter import N8nAdapter
            from adapters.status_sync.services.workflow_sync import WorkflowSync
            from src.core.config import settings

            # 初始化N8n适配器
            n8n_adapter = None
            if settings.n8n.enabled:
                n8n_adapter = N8nAdapter(
                    base_url=settings.n8n.api_url, api_key=settings.n8n.api_key
                )

            # 同步工作流状态
            workflow_sync = WorkflowSync(self.db_session, n8n_adapter)
            success = workflow_sync.sync_workflow_status(workflow_id)

            if success:
                logger.info(f"工作流状态同步成功: {workflow_id} -> {status}")
            else:
                logger.warning(f"工作流状态同步失败: {workflow_id}")

            # 同步系统变量
            if n8n_adapter and status == "active":
                from adapters.status_sync.services.n8n_sync import N8nSync

                n8n_sync = N8nSync(self.db_session, n8n_adapter)
                n8n_sync.sync_variable(
                    "SYSTEM_STATUS_UPDATE",
                    {
                        "type": "workflow",
                        "id": workflow_id,
                        "status": status,
                        "timestamp": context.get("updated_at", ""),
                    },
                )
        except ImportError as e:
            logger.error(f"导入依赖模块失败: {e}")
        except Exception as e:
            logger.exception(f"同步工作流状态失败: {e}")

    def _sync_roadmap_status(self, entity_id: str, status: str, context: Dict[str, Any]) -> None:
        """同步路线图状态

        Args:
            entity_id: 实体ID
            status: 新状态
            context: 上下文信息
        """
        try:
            # 导入N8nSync服务
            from adapters.n8n.adapter import N8nAdapter
            from adapters.status_sync.services.n8n_sync import N8nSync
            from src.core.config import settings

            # 初始化N8n适配器
            if not settings.n8n.enabled:
                logger.debug("N8n未启用，跳过路线图状态同步")
                return

            n8n_adapter = N8nAdapter(base_url=settings.n8n.api_url, api_key=settings.n8n.api_key)

            # 获取完整的上下文信息
            entity_type = context.get("type", "unknown")
            entity_name = context.get("name", entity_id)

            # 同步系统变量
            n8n_sync = N8nSync(self.db_session, n8n_adapter)
            n8n_sync.sync_variable(
                "ROADMAP_STATUS_UPDATE",
                {
                    "type": entity_type,
                    "id": entity_id,
                    "name": entity_name,
                    "status": status,
                    "timestamp": context.get("updated_at", ""),
                },
            )

            # 如果有关联的工作流，也触发工作流状态同步
            workflow_id = context.get("workflow_id")
            if workflow_id:
                from adapters.status_sync.services.execution_sync import ExecutionSync

                execution_sync = ExecutionSync(self.db_session, n8n_adapter)
                execution_id = execution_sync.create_execution(
                    workflow_id,
                    {
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "entity_name": entity_name,
                        "status": status,
                    },
                )

                if execution_id:
                    logger.info(f"触发工作流执行: {workflow_id} (execution: {execution_id})")
                else:
                    logger.warning(f"触发工作流执行失败: {workflow_id}")
        except ImportError as e:
            logger.error(f"导入依赖模块失败: {e}")
        except Exception as e:
            logger.exception(f"同步路线图状态失败: {e}")
