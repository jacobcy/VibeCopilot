"""
工作流数据访问对象模块

提供Workflow、WorkflowStep等实体的数据访问接口。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Workflow, WorkflowExecution, WorkflowStep


class WorkflowRepository(Repository[Workflow]):
    """工作流仓库"""

    def __init__(self, session: Session):
        """初始化工作流仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Workflow)

    def get_with_steps(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流及其关联的步骤

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流对象或None
        """
        return self.session.query(Workflow).filter(Workflow.id == workflow_id).first()

    def get_by_n8n_id(self, n8n_workflow_id: str) -> Optional[Workflow]:
        """根据n8n工作流ID获取工作流

        Args:
            n8n_workflow_id: n8n工作流ID

        Returns:
            工作流对象或None
        """
        return (
            self.session.query(Workflow).filter(Workflow.n8n_workflow_id == n8n_workflow_id).first()
        )

    def get_active_workflows(self) -> List[Workflow]:
        """获取所有活跃的工作流

        Returns:
            工作流对象列表
        """
        return self.session.query(Workflow).filter(Workflow.status == "active").all()


class WorkflowStepRepository(Repository[WorkflowStep]):
    """工作流步骤仓库"""

    def __init__(self, session: Session):
        """初始化工作流步骤仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowStep)

    def get_by_workflow(self, workflow_id: str) -> List[WorkflowStep]:
        """获取指定工作流下的所有步骤

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流步骤对象列表
        """
        return (
            self.session.query(WorkflowStep)
            .filter(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.order)
            .all()
        )

    def reorder_steps(self, workflow_id: str, step_ids: List[str]) -> bool:
        """重新排序工作流步骤

        Args:
            workflow_id: 工作流ID
            step_ids: 按新顺序排列的步骤ID列表

        Returns:
            是否重排成功
        """
        try:
            steps = self.get_by_workflow(workflow_id)
            step_dict = {step.id: step for step in steps}

            # 验证所有步骤ID是否有效
            for step_id in step_ids:
                if step_id not in step_dict:
                    return False

            # 更新步骤顺序
            for i, step_id in enumerate(step_ids):
                step_dict[step_id].order = i

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e


class WorkflowExecutionRepository(Repository[WorkflowExecution]):
    """工作流执行仓库"""

    def __init__(self, session: Session):
        """初始化工作流执行仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowExecution)

    def get_by_workflow(self, workflow_id: str, limit: int = 10) -> List[WorkflowExecution]:
        """获取指定工作流的执行记录

        Args:
            workflow_id: 工作流ID
            limit: 返回记录的数量限制，默认为10

        Returns:
            工作流执行对象列表
        """
        return (
            self.session.query(WorkflowExecution)
            .filter(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_n8n_execution_id(self, n8n_execution_id: str) -> Optional[WorkflowExecution]:
        """根据n8n执行ID获取执行记录

        Args:
            n8n_execution_id: n8n执行ID

        Returns:
            工作流执行对象或None
        """
        return (
            self.session.query(WorkflowExecution)
            .filter(WorkflowExecution.n8n_execution_id == n8n_execution_id)
            .first()
        )

    def filter(self, status: Optional[List[str]] = None) -> List[WorkflowExecution]:
        """根据状态筛选执行记录

        Args:
            status: 状态列表，如["pending", "running"]

        Returns:
            工作流执行对象列表
        """
        query = self.session.query(WorkflowExecution)
        if status:
            query = query.filter(WorkflowExecution.status.in_(status))
        return query.all()
