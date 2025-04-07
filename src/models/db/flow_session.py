"""
工作流会话数据模型模块

定义工作流会话相关的数据模型，包括FlowSession、StageInstance等实体。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class WorkflowDefinition(Base):
    """工作流定义实体模型"""

    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    stages = Column(JSON, nullable=False)  # 可用阶段列表，JSON格式
    source_rule = Column(String, nullable=True)  # 来源规则文件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sessions = relationship(
        "FlowSession", back_populates="workflow_definition", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "stages": self.stages,
            "source_rule": self.source_rule,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            type=data.get("type"),
            description=data.get("description", ""),
            stages=data.get("stages", []),
            source_rule=data.get("source_rule"),
        )


class FlowSession(Base):
    """工作流会话实体模型"""

    __tablename__ = "flow_sessions"

    id = Column(String, primary_key=True)
    workflow_id = Column(
        String, ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, PAUSED, COMPLETED, ABORTED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_stage_id = Column(String, nullable=True)  # 当前阶段ID
    completed_stages = Column(JSON, default=list)  # 已完成阶段ID列表，JSON格式
    context = Column(JSON, nullable=True)  # 会话上下文，JSON格式

    # 关系
    workflow_definition = relationship("WorkflowDefinition", back_populates="sessions")
    stage_instances = relationship(
        "StageInstance", back_populates="session", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "current_stage_id": self.current_stage_id,
            "completed_stages": self.completed_stages,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            workflow_id=data.get("workflow_id"),
            name=data.get("name", ""),
            status=data.get("status", "ACTIVE"),
            current_stage_id=data.get("current_stage_id"),
            completed_stages=data.get("completed_stages", []),
            context=data.get("context", {}),
        )


class StageInstance(Base):
    """阶段实例实体模型"""

    __tablename__ = "stage_instances"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("flow_sessions.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(String, nullable=False)  # 工作流定义中阶段的ID
    name = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, ACTIVE, COMPLETED, FAILED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_items = Column(JSON, default=list)  # 已完成项列表，JSON格式
    context = Column(JSON, nullable=True)  # 阶段上下文，JSON格式
    deliverables = Column(JSON, nullable=True)  # 阶段交付物，JSON格式

    # 关系
    session = relationship("FlowSession", back_populates="stage_instances")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "stage_id": self.stage_id,
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_items": self.completed_items,
            "context": self.context,
            "deliverables": self.deliverables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            session_id=data.get("session_id"),
            stage_id=data.get("stage_id"),
            name=data.get("name", ""),
            status=data.get("status", "PENDING"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            completed_items=data.get("completed_items", []),
            context=data.get("context", {}),
            deliverables=data.get("deliverables", {}),
        )
