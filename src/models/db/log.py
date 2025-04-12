"""
日志数据库模型

定义日志相关的数据库模型，用于持久化系统生成的各类日志
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


def generate_uuid():
    """生成唯一标识符"""
    return str(uuid.uuid4())


class WorkflowLog(Base):
    """工作流日志数据库模型"""

    __tablename__ = "workflow_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(100), nullable=False, index=True)
    workflow_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=True)
    trigger_info = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    result = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    # 关系
    operations = relationship("OperationLog", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "trigger_info": self.trigger_info,
            "result": self.result,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class OperationLog(Base):
    """操作日志数据库模型"""

    __tablename__ = "operation_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    operation_id = Column(String(100), nullable=False, index=True)
    workflow_log_id = Column(String(36), ForeignKey("workflow_logs.id"), nullable=False)
    operation_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=True)
    parameters = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    result = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    # 关系
    workflow = relationship("WorkflowLog", back_populates="operations")
    tasks = relationship("TaskLog", back_populates="operation", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "workflow_log_id": self.workflow_log_id,
            "operation_name": self.operation_name,
            "status": self.status,
            "parameters": self.parameters,
            "result": self.result,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class TaskLog(Base):
    """任务日志数据库模型"""

    __tablename__ = "task_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(100), nullable=False, index=True)
    operation_log_id = Column(String(36), ForeignKey("operation_logs.id"), nullable=False)
    task_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    result = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    operation = relationship("OperationLog", back_populates="tasks")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "operation_log_id": self.operation_log_id,
            "task_name": self.task_name,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PerformanceLog(Base):
    """性能指标日志数据库模型"""

    __tablename__ = "performance_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    metric_name = Column(String(100), nullable=False)
    value = Column(String(50), nullable=False)  # 使用字符串存储，可转换为数值
    context = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    workflow_id = Column(String(100), nullable=True, index=True)
    operation_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "value": self.value,
            "context": self.context,
            "workflow_id": self.workflow_id,
            "operation_id": self.operation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ErrorLog(Base):
    """错误日志数据库模型"""

    __tablename__ = "error_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    error_message = Column(Text, nullable=False)
    error_type = Column(String(100), nullable=False)
    stack_trace = Column(Text, nullable=True)
    workflow_id = Column(String(100), nullable=True, index=True)
    operation_id = Column(String(100), nullable=True, index=True)
    context = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "workflow_id": self.workflow_id,
            "operation_id": self.operation_id,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """审计日志数据库模型"""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)  # 存储为JSON格式的字符串
    workflow_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "workflow_id": self.workflow_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
