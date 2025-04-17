"""
日志仓库

提供对日志数据库模型的访问和操作方法
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.log import AuditLog, ErrorLog, OperationLog, PerformanceLog, TaskLog, WorkflowLog

T = TypeVar("T")


class WorkflowLogRepository(Repository[WorkflowLog]):
    """工作流日志仓库"""

    def __init__(self):
        super().__init__(WorkflowLog)

    def create_workflow_start(self, session: Session, workflow_id: str, workflow_name: str, trigger_info: Dict[str, Any]) -> WorkflowLog:
        """
        记录工作流开始

        Args:
            session: 数据库会话
            workflow_id: 工作流唯一标识
            workflow_name: 工作流名称
            trigger_info: 触发信息

        Returns:
            WorkflowLog: 创建的工作流日志实体
        """
        workflow_log = WorkflowLog(
            workflow_id=workflow_id, workflow_name=workflow_name, trigger_info=json.dumps(trigger_info, ensure_ascii=False), status="started"
        )
        return self.create(session, workflow_log.to_dict())

    def update_workflow_complete(
        self, session: Session, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowLog]:
        """
        更新工作流完成状态

        Args:
            session: 数据库会话
            workflow_id: 工作流唯一标识
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[WorkflowLog]: 更新后的工作流日志实体
        """
        workflow_log = session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()
        if workflow_log:
            workflow_log.status = status
            workflow_log.result = json.dumps(result if result else {}, ensure_ascii=False)
            workflow_log.end_time = datetime.utcnow()
            return workflow_log
        return None

    def get_workflow_logs(self, session: Session, limit: int = 100, offset: int = 0) -> List[WorkflowLog]:
        """获取工作流日志列表"""
        return session.query(WorkflowLog).order_by(desc(WorkflowLog.start_time)).limit(limit).offset(offset).all()

    def get_workflow_log_by_id(self, session: Session, workflow_id: str) -> Optional[WorkflowLog]:
        """根据工作流ID获取最新日志"""
        return session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()


class OperationLogRepository(Repository[OperationLog]):
    """操作日志仓库"""

    def __init__(self):
        super().__init__(OperationLog)

    def create_operation_start(
        self, session: Session, operation_id: str, workflow_id: str, operation_name: str, parameters: Dict[str, Any]
    ) -> OperationLog:
        """
        记录操作开始

        Args:
            session: 数据库会话
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            operation_name: 操作名称
            parameters: 操作参数

        Returns:
            OperationLog: 创建的操作日志实体
        """
        workflow_log = session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()

        if not workflow_log:
            raise ValueError(f"找不到工作流日志记录: {workflow_id}")

        operation_log = OperationLog(
            operation_id=operation_id,
            workflow_log_id=workflow_log.id,
            operation_name=operation_name,
            parameters=json.dumps(parameters, ensure_ascii=False),
            status="started",
        )
        return self.create(session, operation_log.to_dict())

    def update_operation_complete(
        self, session: Session, operation_id: str, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> Optional[OperationLog]:
        """
        更新操作完成状态

        Args:
            session: 数据库会话
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[OperationLog]: 更新后的操作日志实体
        """
        operation_log = session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()

        if operation_log:
            operation_log.status = status
            operation_log.result = json.dumps(result if result else {}, ensure_ascii=False)
            operation_log.end_time = datetime.utcnow()
            return operation_log
        return None

    def get_operations_for_workflow(self, session: Session, workflow_id: str) -> List[OperationLog]:
        """获取指定工作流的所有操作日志"""
        workflow_log = session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()
        if workflow_log:
            return session.query(OperationLog).filter(OperationLog.workflow_log_id == workflow_log.id).all()
        return []


class TaskLogRepository(Repository[TaskLog]):
    """任务日志仓库"""

    def __init__(self):
        super().__init__(TaskLog)

    def log_task_result(
        self,
        session: Session,
        task_id: str,
        operation_id: str,
        workflow_id: str,
        task_name: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> TaskLog:
        """
        记录任务结果

        Args:
            session: 数据库会话
            task_id: 任务唯一标识
            operation_id: 关联的操作ID
            workflow_id: 关联的工作流ID
            task_name: 任务名称
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            TaskLog: 创建的任务日志实体
        """
        operation_log = session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()

        if not operation_log:
            raise ValueError(f"找不到操作日志记录: {operation_id}")

        task_log = TaskLog(
            task_id=task_id,
            operation_log_id=operation_log.id,
            task_name=task_name,
            status=status,
            result=json.dumps(result if result else {}, ensure_ascii=False),
        )
        return self.create(session, task_log.to_dict())

    def get_tasks_for_operation(self, session: Session, operation_id: str) -> List[TaskLog]:
        """获取指定操作的所有任务日志"""
        operation_log = session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()
        if operation_log:
            return session.query(TaskLog).filter(TaskLog.operation_log_id == operation_log.id).all()
        return []

    def log_activity(self, session: Session, task_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """记录与任务相关的活动日志 (可能需要实现)"""
        # Example implementation - Adapt based on actual needs/model
        # This might belong in a different model/repo if TaskLog is just for results
        activity_log = TaskLog(  # Or a different model like TaskActivityLog
            task_id=task_id,
            # operation_log_id=... # Link appropriately if needed
            task_name=action,  # Or use a dedicated 'action' field
            status="activity",  # Differentiate from task results
            result=json.dumps(details if details else {}, ensure_ascii=False),
            created_at=datetime.utcnow(),  # Explicitly set timestamp if model doesn't auto-set
        )
        session.add(activity_log)
        # No commit needed
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"记录任务活动: TaskID={task_id}, Action={action}")


class PerformanceLogRepository(Repository[PerformanceLog]):
    """性能日志仓库"""

    def __init__(self):
        super().__init__(PerformanceLog)

    def log_performance_metric(
        self,
        session: Session,
        metric_name: str,
        value: Union[int, float],
        context: Dict[str, Any],
        workflow_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> PerformanceLog:
        """
        记录性能指标

        Args:
            session: 数据库会话
            metric_name: 指标名称
            value: 指标值
            context: 上下文信息
            workflow_id: 关联的工作流ID（可选）
            operation_id: 关联的操作ID（可选）

        Returns:
            PerformanceLog: 创建的性能日志实体
        """
        performance_log = PerformanceLog(
            metric_name=metric_name,
            value=str(value),
            context=json.dumps(context, ensure_ascii=False),
            workflow_id=workflow_id,
            operation_id=operation_id,
        )
        return self.create(session, performance_log.to_dict())

    def get_metrics_by_name(self, session: Session, metric_name: str, limit: int = 100) -> List[PerformanceLog]:
        """获取指定名称的性能指标"""
        return (
            session.query(PerformanceLog)
            .filter(PerformanceLog.metric_name == metric_name)
            .order_by(desc(PerformanceLog.created_at))
            .limit(limit)
            .all()
        )

    def get_metrics_for_workflow(self, session: Session, workflow_id: str) -> List[PerformanceLog]:
        """获取指定工作流的所有性能指标"""
        return session.query(PerformanceLog).filter(PerformanceLog.workflow_id == workflow_id).order_by(desc(PerformanceLog.created_at)).all()


class ErrorLogRepository(Repository[ErrorLog]):
    """错误日志仓库"""

    def __init__(self):
        super().__init__(ErrorLog)

    def log_error(
        self,
        session: Session,
        error_message: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        workflow_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorLog:
        """
        记录错误

        Args:
            session: 数据库会话
            error_message: 错误消息
            error_type: 错误类型
            stack_trace: 堆栈跟踪（可选）
            workflow_id: 关联的工作流ID（可选）
            operation_id: 关联的操作ID（可选）
            context: 错误发生时的上下文信息（可选）

        Returns:
            ErrorLog: 创建的错误日志实体
        """
        error_log = ErrorLog(
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            workflow_id=workflow_id,
            operation_id=operation_id,
            context=json.dumps(context if context else {}, ensure_ascii=False),
        )
        return self.create(session, error_log.to_dict())

    def get_recent_errors(self, session: Session, limit: int = 50) -> List[ErrorLog]:
        """获取最近的错误日志"""
        return session.query(ErrorLog).order_by(desc(ErrorLog.created_at)).limit(limit).all()

    def get_errors_for_workflow(self, session: Session, workflow_id: str) -> List[ErrorLog]:
        """获取指定工作流的所有错误日志"""
        return session.query(ErrorLog).filter(ErrorLog.workflow_id == workflow_id).order_by(desc(ErrorLog.created_at)).all()


class AuditLogRepository(Repository[AuditLog]):
    """审计日志仓库"""

    def __init__(self):
        super().__init__(AuditLog)

    def log_audit(
        self,
        session: Session,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
        workflow_id: Optional[str] = None,
    ) -> AuditLog:
        """
        记录审计信息

        Args:
            session: 数据库会话
            user_id: 用户ID
            action: 执行的操作
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            workflow_id: 关联的工作流ID（可选）

        Returns:
            AuditLog: 创建的审计日志实体
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details, ensure_ascii=False),
            workflow_id=workflow_id,
        )
        return self.create(session, audit_log.to_dict())

    def get_audit_logs_by_user(self, session: Session, user_id: str, limit: int = 100) -> List[AuditLog]:
        """获取指定用户的所有审计日志"""
        return session.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(desc(AuditLog.created_at)).limit(limit).all()

    def get_audit_logs_by_resource(self, session: Session, resource_type: str, resource_id: str) -> List[AuditLog]:
        """获取指定资源的所有审计日志"""
        return (
            session.query(AuditLog)
            .filter(AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id)
            .order_by(desc(AuditLog.created_at))
            .all()
        )
