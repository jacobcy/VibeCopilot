"""
工作流同步服务

负责同步工作流状态到n8n外部系统
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from adapters.n8n.adapter import N8nAdapter
from src.db.repositories.workflow_repository import WorkflowRepository

logger = logging.getLogger(__name__)


class WorkflowSync:
    """工作流同步服务类"""

    def __init__(
        self,
        db_session: Session,
        n8n_adapter: Optional[N8nAdapter] = None,
    ):
        """初始化工作流同步服务

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器实例
        """
        self.db_session = db_session
        self.workflow_repo = WorkflowRepository(db_session)
        self.n8n_adapter = n8n_adapter

    def sync_workflow_status(self, workflow_id: str) -> bool:
        """同步工作流状态到n8n

        Args:
            workflow_id: 工作流ID

        Returns:
            是否同步成功
        """
        try:
            # 获取工作流信息
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return False

            # 获取n8n中的工作流信息
            if workflow.n8n_workflow_id and self.n8n_adapter:
                n8n_workflow = self.n8n_adapter.get_workflow(workflow.n8n_workflow_id)
                if not n8n_workflow:
                    logger.warning(f"n8n中不存在此工作流: {workflow.n8n_workflow_id}")
                    return False

                # 更新工作流状态
                if workflow.status == "active" and not n8n_workflow.get("active", False):
                    self.n8n_adapter.activate_workflow(workflow.n8n_workflow_id)
                    logger.info(f"激活n8n工作流: {workflow.n8n_workflow_id}")
                elif workflow.status != "active" and n8n_workflow.get("active", False):
                    self.n8n_adapter.deactivate_workflow(workflow.n8n_workflow_id)
                    logger.info(f"停用n8n工作流: {workflow.n8n_workflow_id}")

            return True
        except Exception as e:
            logger.exception(f"同步工作流状态失败: {str(e)}")
            return False

    def create_n8n_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """在n8n中创建工作流

        Args:
            workflow_id: 本地工作流ID
            workflow_data: n8n工作流数据

        Returns:
            是否创建成功
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return False

            # 获取工作流信息
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return False

            # 创建n8n工作流
            result = self.n8n_adapter.create_workflow(workflow_data)
            if not result:
                logger.error("创建n8n工作流失败")
                return False

            # 更新工作流n8n ID
            workflow.n8n_workflow_id = result.get("id")
            if workflow.status == "active":
                self.n8n_adapter.activate_workflow(workflow.n8n_workflow_id)

            self.db_session.commit()
            logger.info(f"成功创建n8n工作流: {workflow.n8n_workflow_id}")
            return True

        except Exception as e:
            logger.exception(f"创建n8n工作流失败: {str(e)}")
            self.db_session.rollback()
            return False

    def import_n8n_workflows(self) -> int:
        """从n8n导入所有工作流

        Returns:
            导入的工作流数量
        """
        try:
            if not self.n8n_adapter:
                logger.error("n8n适配器未初始化")
                return 0

            # 获取所有n8n工作流
            workflows = self.n8n_adapter.get_all_workflows()
            if not workflows:
                logger.info("n8n中没有工作流")
                return 0

            import_count = 0
            for n8n_workflow in workflows:
                # 查找是否已存在
                existing = self.workflow_repo.get_by_n8n_workflow_id(n8n_workflow.get("id"))
                if existing:
                    logger.debug(f"工作流已存在: {n8n_workflow.get('name')}")
                    continue

                # 创建新工作流
                workflow_data = {
                    "name": n8n_workflow.get("name"),
                    "description": n8n_workflow.get("description", "从n8n导入的工作流"),
                    "n8n_workflow_id": n8n_workflow.get("id"),
                    "status": "active" if n8n_workflow.get("active") else "inactive",
                    "metadata": {
                        "n8n_tags": n8n_workflow.get("tags", []),
                        "n8n_created_at": n8n_workflow.get("createdAt"),
                        "n8n_updated_at": n8n_workflow.get("updatedAt"),
                    },
                }

                self.workflow_repo.create(**workflow_data)
                import_count += 1
                logger.info(f"导入工作流: {workflow_data['name']}")

            self.db_session.commit()
            return import_count

        except Exception as e:
            logger.exception(f"导入n8n工作流失败: {str(e)}")
            self.db_session.rollback()
            return 0
