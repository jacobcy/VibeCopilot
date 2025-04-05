"""
工作流数据访问对象模块

提供Workflow、WorkflowStep、WorkflowExecution等实体的数据访问接口。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models.roadmap import Label
from src.db.models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepExecution,
)
from src.db.repository import Repository


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
        return self.session.query(Workflow).filter(Workflow.n8n_workflow_id == n8n_workflow_id).first()

    def get_active_workflows(self) -> List[Workflow]:
        """获取所有活跃的工作流

        Returns:
            工作流对象列表
        """
        return self.session.query(Workflow).filter(Workflow.status == "active").all()

    def add_label(self, workflow_id: str, label_id: str) -> bool:
        """为工作流添加标签

        Args:
            workflow_id: 工作流ID
            label_id: 标签ID

        Returns:
            是否添加成功
        """
        try:
            workflow = self.get_by_id(workflow_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not workflow or not label:
                return False

            if label not in workflow.labels:
                workflow.labels.append(label)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            raise e

    def remove_label(self, workflow_id: str, label_id: str) -> bool:
        """移除工作流标签

        Args:
            workflow_id: 工作流ID
            label_id: 标签ID

        Returns:
            是否移除成功
        """
        try:
            workflow = self.get_by_id(workflow_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not workflow or not label:
                return False

            if label in workflow.labels:
                workflow.labels.remove(label)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            raise e


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

    def get_by_workflow(self, workflow_id: str) -> List[WorkflowExecution]:
        """获取指定工作流的所有执行记录

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流执行对象列表
        """
        return (
            self.session.query(WorkflowExecution)
            .filter(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
            .all()
        )

    def get_by_n8n_execution_id(self, n8n_execution_id: str) -> Optional[WorkflowExecution]:
        """根据n8n执行ID获取工作流执行记录

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

    def get_recent_executions(self, limit: int = 10) -> List[WorkflowExecution]:
        """获取最近的工作流执行记录

        Args:
            limit: 返回记录数量限制

        Returns:
            工作流执行对象列表
        """
        return (
            self.session.query(WorkflowExecution)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
            .all()
        )


class WorkflowStepExecutionRepository(Repository[WorkflowStepExecution]):
    """工作流步骤执行仓库"""

    def __init__(self, session: Session):
        """初始化工作流步骤执行仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowStepExecution)

    def get_by_workflow_execution(self, workflow_execution_id: str) -> List[WorkflowStepExecution]:
        """获取指定工作流执行的所有步骤执行记录

        Args:
            workflow_execution_id: 工作流执行ID

        Returns:
            工作流步骤执行对象列表
        """
        return (
            self.session.query(WorkflowStepExecution)
            .filter(WorkflowStepExecution.workflow_execution_id == workflow_execution_id)
            .all()
        )

    def get_current_step(self, workflow_execution_id: str) -> Optional[WorkflowStepExecution]:
        """获取当前正在执行的步骤

        Args:
            workflow_execution_id: 工作流执行ID

        Returns:
            当前步骤执行对象或None
        """
        return (
            self.session.query(WorkflowStepExecution)
            .filter(
                WorkflowStepExecution.workflow_execution_id == workflow_execution_id,
                WorkflowStepExecution.status == "running",
            )
            .first()
        )
