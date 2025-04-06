"""
执行同步服务

负责同步工作流执行状态和结果
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from adapters.n8n.adapter import N8nAdapter
from src.db.repositories import WorkflowExecutionRepository, WorkflowRepository

logger = logging.getLogger(__name__)


class ExecutionSync:
    """执行同步服务类"""

    def __init__(
        self,
        db_session: Session,
        n8n_adapter: Optional[N8nAdapter] = None,
    ):
        """初始化执行同步服务

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器实例
        """
        self.db_session = db_session
        self.execution_repo = WorkflowExecutionRepository(db_session)
        self.workflow_repo = WorkflowRepository(db_session)
        self.n8n_adapter = n8n_adapter

    def sync_execution_status(self, execution_id: str) -> bool:
        """同步执行状态

        Args:
            execution_id: 执行ID

        Returns:
            是否同步成功
        """
        try:
            # 获取执行信息
            execution = self.execution_repo.get_by_id(execution_id)
            if not execution:
                logger.error(f"执行不存在: {execution_id}")
                return False

            # 获取n8n中的执行信息
            if execution.n8n_execution_id and self.n8n_adapter:
                n8n_execution = self.n8n_adapter.get_execution(execution.n8n_execution_id)
                if not n8n_execution:
                    logger.warning(f"n8n中不存在此执行: {execution.n8n_execution_id}")
                    return False

                # 更新执行状态
                n8n_status = n8n_execution.get("status", "")
                if n8n_status == "waiting":
                    execution.status = "pending"
                elif n8n_status == "running":
                    execution.status = "running"
                elif n8n_status == "success":
                    execution.status = "completed"
                    execution.result = n8n_execution.get("data", {})
                    execution.completed_at = datetime.now()
                elif n8n_status in ["error", "failed"]:
                    execution.status = "failed"
                    execution.error = n8n_execution.get("error", {})
                    execution.completed_at = datetime.now()

                self.db_session.commit()
                logger.info(f"更新执行状态: {execution_id} -> {execution.status}")

            return True
        except Exception as e:
            logger.exception(f"同步执行状态失败: {str(e)}")
            self.db_session.rollback()
            return False

    def sync_all_pending_executions(self) -> int:
        """同步所有待处理的执行

        Returns:
            同步的执行数量
        """
        try:
            # 获取所有待处理的执行
            executions = self.execution_repo.filter(status=["pending", "running"])
            if not executions:
                return 0

            sync_count = 0
            for execution in executions:
                if self.sync_execution_status(execution.id):
                    sync_count += 1

            return sync_count
        except Exception as e:
            logger.exception(f"同步所有待处理执行失败: {str(e)}")
            return 0

    def create_execution(self, workflow_id: str, params: Dict[str, Any] = None) -> Optional[str]:
        """创建执行记录并启动n8n工作流

        Args:
            workflow_id: 工作流ID
            params: 执行参数

        Returns:
            执行ID，如果失败则返回None
        """
        try:
            # 获取工作流信息
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return None

            # 检查工作流状态
            if workflow.status != "active":
                logger.error(f"工作流未激活: {workflow_id}")
                return None

            # 创建执行记录
            execution_data = {
                "workflow_id": workflow_id,
                "status": "pending",
                "params": params or {},
                "started_at": datetime.now(),
            }

            execution = self.execution_repo.create(**execution_data)

            # 如果有n8n工作流ID，则启动n8n工作流
            if workflow.n8n_workflow_id and self.n8n_adapter:
                try:
                    # 启动n8n工作流
                    result = self.n8n_adapter.trigger_workflow(
                        workflow.n8n_workflow_id, {"execution_id": execution.id, **execution.params}
                    )

                    if result:
                        # 更新执行记录
                        execution.n8n_execution_id = result.get("id")
                        execution.status = "running"
                        self.db_session.commit()
                        logger.info(f"启动n8n工作流成功: {execution.id}")
                    else:
                        logger.error(f"启动n8n工作流失败: {workflow.n8n_workflow_id}")
                        execution.status = "failed"
                        execution.error = {"message": "启动n8n工作流失败"}
                        execution.completed_at = datetime.now()
                        self.db_session.commit()
                except Exception as e:
                    logger.exception(f"启动n8n工作流异常: {str(e)}")
                    execution.status = "failed"
                    execution.error = {"message": str(e)}
                    execution.completed_at = datetime.now()
                    self.db_session.commit()

            return execution.id
        except Exception as e:
            logger.exception(f"创建执行记录失败: {str(e)}")
            self.db_session.rollback()
            return None

    def get_executions_by_workflow(self, workflow_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取工作流的执行记录

        Args:
            workflow_id: 工作流ID
            limit: 限制数量

        Returns:
            执行记录列表
        """
        try:
            executions = self.execution_repo.get_by_workflow(workflow_id, limit)
            return [e.to_dict() for e in executions]
        except Exception as e:
            logger.exception(f"获取工作流执行记录失败: {str(e)}")
            return []
