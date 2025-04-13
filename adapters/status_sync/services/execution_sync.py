"""
执行同步服务

负责同步执行状态到外部系统
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import WorkflowDefinitionRepository
from src.models.db import WorkflowDefinition

logger = logging.getLogger(__name__)


class ExecutionSync:
    """执行同步服务类"""

    def __init__(
        self,
        db_session: Session,
        n8n_adapter=None,
    ):
        """初始化执行同步服务

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器，可选
        """
        self.db_session = db_session
        self.n8n_adapter = n8n_adapter
        self.workflow_repo = WorkflowDefinitionRepository(db_session)
        logger.info("ExecutionSync服务已初始化")

    def sync_execution_status(self, execution_id: str) -> bool:
        """同步执行状态到外部系统

        Args:
            execution_id: 执行ID

        Returns:
            是否同步成功
        """
        # 获取执行记录
        # TODO: 添加执行记录仓库实现
        logger.info(f"同步执行状态: {execution_id}")

        # 如果有n8n适配器，同步到n8n
        if self.n8n_adapter:
            try:
                return self.n8n_adapter.sync_execution(execution_id)
            except Exception as e:
                logger.error(f"同步到n8n时出错: {e}")
                return False

        return True

    def create_execution(self, workflow_id: str, context: Dict[str, Any]) -> Optional[str]:
        """创建执行记录

        Args:
            workflow_id: 工作流ID
            context: 执行上下文

        Returns:
            执行ID，如果创建失败则返回None
        """
        try:
            # 验证工作流存在
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return None

            # 生成执行ID
            execution_id = f"exec_{uuid.uuid4().hex[:8]}"

            # TODO: 保存执行记录到数据库

            # 如果有n8n适配器，创建n8n执行
            if self.n8n_adapter:
                try:
                    n8n_result = self.n8n_adapter.create_execution(workflow_id, context)
                    if n8n_result.get("success"):
                        # TODO: 更新执行记录的外部ID
                        pass
                except Exception as e:
                    logger.error(f"创建n8n执行时出错: {e}")

            logger.info(f"创建执行记录成功: {execution_id}")
            return execution_id
        except Exception as e:
            logger.exception(f"创建执行记录失败: {e}")
            return None

    def get_workflow_executions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取工作流的执行记录

        Args:
            workflow_id: 工作流ID

        Returns:
            执行记录列表
        """
        # 验证工作流存在
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            logger.error(f"工作流不存在: {workflow_id}")
            return []

        # TODO: 从数据库获取执行记录

        # 临时返回空列表
        logger.info(f"获取工作流执行记录: {workflow_id}")
        return []
