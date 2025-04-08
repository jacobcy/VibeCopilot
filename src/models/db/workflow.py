"""
工作流数据模型模块

定义工作流相关的数据模型，包括Workflow、WorkflowStep、WorkflowExecution等实体。
"""

import json
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Workflow(Base):
    """工作流数据库模型，定义一个完整的流程"""

    __tablename__ = "workflows"

    id = Column(String(50), primary_key=True, default=lambda: f"workflow_{uuid.uuid4().hex[:8]}")
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    tags = Column(Text, nullable=True)  # 存储为JSON字符串
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.order")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化Workflow，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"workflow_{uuid.uuid4().hex[:8]}"

        # 处理标签格式
        if "tags" in kwargs and isinstance(kwargs["tags"], list):
            kwargs["tags"] = json.dumps(kwargs["tags"])

        # 确保时间戳
        if not kwargs.get("created_at"):
            kwargs["created_at"] = datetime.now().isoformat()
        if not kwargs.get("updated_at"):
            kwargs["updated_at"] = datetime.now().isoformat()

        super().__init__(**kwargs)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "is_active": self.is_active,
            "tags": json.loads(self.tags) if self.tags else [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "steps": [step.to_dict() for step in self.steps] if self.steps else [],
        }


class WorkflowStep(Base):
    """工作流步骤数据库模型，表示工作流中的一个步骤"""

    __tablename__ = "workflow_steps"

    id = Column(String(50), primary_key=True, default=lambda: f"step_{uuid.uuid4().hex[:8]}")
    workflow_id = Column(String(50), ForeignKey("workflows.id"))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    action = Column(String(200), nullable=False)  # 执行的动作类型
    parameters = Column(Text, nullable=True)  # 存储为JSON字符串
    order = Column(Integer, nullable=False)  # 在工作流中的顺序
    is_required = Column(Boolean, default=True)
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    workflow = relationship("Workflow", back_populates="steps")
    executions = relationship("WorkflowStepExecution", back_populates="step", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化WorkflowStep，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"step_{uuid.uuid4().hex[:8]}"

        # 处理参数格式
        if "parameters" in kwargs and not isinstance(kwargs["parameters"], str):
            kwargs["parameters"] = json.dumps(kwargs["parameters"])

        # 确保时间戳
        if not kwargs.get("created_at"):
            kwargs["created_at"] = datetime.now().isoformat()
        if not kwargs.get("updated_at"):
            kwargs["updated_at"] = datetime.now().isoformat()

        super().__init__(**kwargs)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "parameters": json.loads(self.parameters) if self.parameters else {},
            "order": self.order,
            "is_required": self.is_required,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


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
    step_executions = relationship("WorkflowStepExecution", back_populates="workflow_execution", cascade="all, delete-orphan")

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
    workflow_execution_id = Column(String, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String, ForeignKey("workflow_steps.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, failed, skipped
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)  # 执行结果，JSON格式
    error = Column(Text, nullable=True)  # 错误信息
    retry_count = Column(Integer, default=0)  # 重试次数

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
            "retry_count": self.retry_count,
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
            retry_count=data.get("retry_count", 0),
        )
