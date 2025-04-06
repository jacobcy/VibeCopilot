"""
工作流数据模型模块

定义工作流相关的数据模型，包括Workflow、WorkflowStep、WorkflowExecution等实体。
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from .base import Base

# 工作流标签关联表
# workflow_label = Table(
#     "workflow_label_association",
#     Base.metadata,
#     Column("workflow_id", String, ForeignKey("workflows.id", ondelete="CASCADE")),
#     Column("label_id", String, ForeignKey("labels.id", ondelete="CASCADE")),
# )


class Workflow(Base):
    """工作流实体模型"""

    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, inactive, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    n8n_workflow_id = Column(String, nullable=True)  # n8n中的工作流ID
    n8n_workflow_url = Column(String, nullable=True)  # n8n中的工作流URL
    config = Column(JSON, nullable=True)  # 工作流配置，JSON格式

    # 关系
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )
    # 移除标签关系
    # labels = relationship("Label", secondary=workflow_label, back_populates="workflows")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "n8n_workflow_id": self.n8n_workflow_id,
            "n8n_workflow_url": self.n8n_workflow_url,
            "config": self.config,
            # 移除标签属性
            # "labels": [label.name for label in self.labels] if self.labels else [],
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            n8n_workflow_id=data.get("n8n_workflow_id"),
            n8n_workflow_url=data.get("n8n_workflow_url"),
            config=data.get("config"),
        )


class WorkflowStep(Base):
    """工作流步骤实体模型"""

    __tablename__ = "workflow_steps"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)  # 步骤顺序
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    step_type = Column(String, nullable=False)  # 步骤类型: task, approval, notification, etc.
    config = Column(JSON, nullable=True)  # 步骤配置，JSON格式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="steps")
    executions = relationship(
        "WorkflowStepExecution", back_populates="step", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "workflow_id": self.workflow_id,
            "step_type": self.step_type,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            order=data.get("order", 0),
            workflow_id=data.get("workflow_id"),
            step_type=data.get("step_type", "task"),
            config=data.get("config"),
        )


class WorkflowExecution(Base):
    """工作流执行实体模型"""

    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)  # 执行结果，JSON格式
    error = Column(Text, nullable=True)  # 错误信息
    n8n_execution_id = Column(String, nullable=True)  # n8n中的执行ID
    n8n_execution_url = Column(String, nullable=True)  # n8n中的执行URL
    context = Column(JSON, nullable=True)  # 执行上下文，JSON格式

    # 关系
    workflow = relationship("Workflow", back_populates="executions")
    step_executions = relationship(
        "WorkflowStepExecution", back_populates="workflow_execution", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "n8n_execution_id": self.n8n_execution_id,
            "n8n_execution_url": self.n8n_execution_url,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            workflow_id=data.get("workflow_id"),
            status=data.get("status", "pending"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=data.get("error"),
            n8n_execution_id=data.get("n8n_execution_id"),
            n8n_execution_url=data.get("n8n_execution_url"),
            context=data.get("context"),
        )


class WorkflowStepExecution(Base):
    """工作流步骤执行实体模型"""

    __tablename__ = "workflow_step_executions"

    id = Column(String, primary_key=True)
    workflow_execution_id = Column(
        String, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    step_id = Column(String, ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)  # 执行结果，JSON格式
    error = Column(Text, nullable=True)  # 错误信息
    context = Column(JSON, nullable=True)  # 执行上下文，JSON格式

    # 关系
    workflow_execution = relationship("WorkflowExecution", back_populates="step_executions")
    step = relationship("WorkflowStep", back_populates="executions")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_execution_id": self.workflow_execution_id,
            "step_id": self.step_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            workflow_execution_id=data.get("workflow_execution_id"),
            step_id=data.get("step_id"),
            status=data.get("status", "pending"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=data.get("error"),
            context=data.get("context"),
        )
