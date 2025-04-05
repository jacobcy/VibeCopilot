"""
状态同步适配器模块

负责将本地SQLite状态库中的任务状态同步到外部系统（如GitHub Projects和n8n Workflow）。
作为Agent核心逻辑与外部系统集成的桥梁，解耦核心业务逻辑与外部系统交互。
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from src.adapters.n8n_adapter import N8nAdapter
from src.db.models.workflow import Workflow, WorkflowExecution, WorkflowStep
from src.db.repositories.workflow_repository import WorkflowExecutionRepository, WorkflowRepository

logger = logging.getLogger(__name__)


class StatusSyncAdapter:
    """状态同步适配器类"""

    def __init__(
        self,
        db_session: Session,
        n8n_adapter: Optional[N8nAdapter] = None,
        n8n_base_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None,
    ):
        """初始化状态同步适配器

        Args:
            db_session: 数据库会话
            n8n_adapter: n8n适配器实例，如果未提供则创建新实例
            n8n_base_url: n8n API基础URL，如果未提供则从环境变量获取
            n8n_api_key: n8n API密钥，如果未提供则从环境变量获取
        """
        self.db_session = db_session
        self.workflow_repo = WorkflowRepository(db_session)
        self.execution_repo = WorkflowExecutionRepository(db_session)

        # 初始化n8n适配器
        self.n8n_adapter = n8n_adapter or N8nAdapter(
            base_url=n8n_base_url, api_key=n8n_api_key
        )

        # 状态映射配置
        self.status_map = {
            "pending": {"n8n_workflow": "notification_workflow", "payload": {"status": "pending"}},
            "running": {"n8n_workflow": "execution_workflow", "payload": {"status": "running"}},
            "completed": {"n8n_workflow": "completion_workflow", "payload": {"status": "completed"}},
            "failed": {"n8n_workflow": "failure_workflow", "payload": {"status": "failed"}},
        }

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
            if workflow.n8n_workflow_id:
                n8n_workflow = self.n8n_adapter.get_workflow(workflow.n8n_workflow_id)
                if not n8n_workflow:
                    logger.warning(f"n8n中不存在此工作流: {workflow.n8n_workflow_id}")
                    return False

                # 更新工作流状态
                if workflow.status == "active" and not n8n_workflow.get("active", False):
                    self.n8n_adapter.activate_workflow(workflow.n8n_workflow_id)
                elif workflow.status != "active" and n8n_workflow.get("active", False):
                    self.n8n_adapter.deactivate_workflow(workflow.n8n_workflow_id)

            return True
        except Exception as e:
            logger.exception(f"同步工作流状态失败: {str(e)}")
            return False

    def sync_execution_status(self, execution_id: str) -> bool:
        """同步执行状态到n8n

        Args:
            execution_id: 执行ID

        Returns:
            是否同步成功
        """
        try:
            # 获取执行信息
            execution = self.execution_repo.get_by_id(execution_id)
            if not execution:
                logger.error(f"执行记录不存在: {execution_id}")
                return False

            # 获取工作流信息
            workflow = self.workflow_repo.get_by_id(execution.workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {execution.workflow_id}")
                return False

            # 检查状态是否需要同步
            status = execution.status.lower()
            if status not in self.status_map:
                logger.warning(f"未配置的状态: {status}")
                return True  # 不需要同步的状态也视为成功

            # 获取对应的n8n工作流和负载
            workflow_key = self.status_map[status].get("n8n_workflow")
            payload = self.status_map[status].get("payload", {}).copy()

            # 添加执行上下文到负载
            payload.update({
                "execution_id": execution.id,
                "workflow_id": execution.workflow_id,
                "workflow_name": workflow.name,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "result": execution.result,
                "error": execution.error,
                "context": execution.context,
            })

            # 如果有n8n工作流ID，则触发对应的工作流
            if workflow.n8n_workflow_id and workflow_key:
                result = self.n8n_adapter.trigger_workflow(workflow.n8n_workflow_id, payload)
                if result:
                    # 更新n8n执行ID
                    execution.n8n_execution_id = result.get("id")
                    self.db_session.commit()
                    logger.info(f"成功触发n8n工作流: {workflow.n8n_workflow_id}, 执行ID: {result.get('id')}")
                    return True
                else:
                    logger.error(f"触发n8n工作流失败: {workflow.n8n_workflow_id}")
                    return False

            return True
        except Exception as e:
            logger.exception(f"同步执行状态失败: {str(e)}")
            return False

    def sync_pending_executions(self) -> int:
        """同步所有待处理的执行状态

        Returns:
            成功同步的执行数量
        """
        try:
            # 获取所有状态为pending或running的执行
            pending_executions = self.execution_repo.filter(
                status=["pending", "running"]
            )
            
            success_count = 0
            for execution in pending_executions:
                if self.sync_execution_status(execution.id):
                    success_count += 1
            
            return success_count
        except Exception as e:
            logger.exception(f"同步待处理执行状态失败: {str(e)}")
            return 0

    def update_execution_from_n8n(self, n8n_execution_id: str) -> bool:
        """从n8n更新执行状态

        Args:
            n8n_execution_id: n8n执行ID

        Returns:
            是否更新成功
        """
        try:
            # 获取n8n执行信息
            n8n_execution = self.n8n_adapter.get_execution(n8n_execution_id)
            if not n8n_execution:
                logger.error(f"n8n执行不存在: {n8n_execution_id}")
                return False

            # 查找对应的本地执行记录
            execution = self.execution_repo.get_by_n8n_execution_id(n8n_execution_id)
            if not execution:
                logger.error(f"未找到对应的本地执行记录: {n8n_execution_id}")
                return False

            # 更新执行状态
            n8n_status = n8n_execution.get("status", "").lower()
            if n8n_status == "running":
                execution.status = "running"
            elif n8n_status == "success":
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.result = n8n_execution.get("data", {})
            elif n8n_status in ["error", "failed", "crashed"]:
                execution.status = "failed"
                execution.completed_at = datetime.utcnow()
                execution.error = json.dumps(n8n_execution.get("error", {}))

            # 更新执行URL
            if "url" in n8n_execution:
                execution.n8n_execution_url = n8n_execution["url"]

            self.db_session.commit()
            logger.info(f"成功从n8n更新执行状态: {n8n_execution_id}")
            return True
        except Exception as e:
            logger.exception(f"从n8n更新执行状态失败: {str(e)}")
            self.db_session.rollback()
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

            # 更新本地工作流信息
            workflow.n8n_workflow_id = result.get("id")
            workflow.n8n_workflow_url = f"{self.n8n_adapter.base_url}/workflow/{result.get('id')}"
            self.db_session.commit()

            logger.info(f"成功创建n8n工作流: {result.get('id')}")
            return True
        except Exception as e:
            logger.exception(f"创建n8n工作流失败: {str(e)}")
            self.db_session.rollback()
            return False

    def import_n8n_workflows(self) -> int:
        """从n8n导入工作流

        Returns:
            导入的工作流数量
        """
        try:
            # 获取n8n中的所有工作流
            n8n_workflows = self.n8n_adapter.get_workflows()
            if not n8n_workflows:
                logger.warning("n8n中没有工作流")
                return 0

            import_count = 0
            for n8n_workflow in n8n_workflows:
                n8n_id = n8n_workflow.get("id")
                if not n8n_id:
                    continue

                # 检查是否已存在
                existing = self.workflow_repo.get_by_n8n_id(n8n_id)
                if existing:
                    continue

                # 创建本地工作流记录
                workflow_data = {
                    "id": str(uuid.uuid4()),
                    "name": n8n_workflow.get("name", "导入的工作流"),
                    "description": n8n_workflow.get("description", "从n8n导入的工作流"),
                    "status": "active" if n8n_workflow.get("active", False) else "inactive",
                    "n8n_workflow_id": n8n_id,
                    "n8n_workflow_url": f"{self.n8n_adapter.base_url}/workflow/{n8n_id}",
                    "config": n8n_workflow,
                }
                
                self.workflow_repo.create(workflow_data)
                import_count += 1
                logger.info(f"成功导入n8n工作流: {n8n_id}")

            return import_count
        except Exception as e:
            logger.exception(f"导入n8n工作流失败: {str(e)}")
            self.db_session.rollback()
            return 0
