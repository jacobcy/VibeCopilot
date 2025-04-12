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

    def __init__(self, session: Session):
        super().__init__(session, WorkflowLog)

    def create_workflow_start(self, workflow_id: str, workflow_name: str, trigger_info: Dict[str, Any]) -> WorkflowLog:
        """
        记录工作流开始

        Args:
            workflow_id: 工作流唯一标识
            workflow_name: 工作流名称
            trigger_info: 触发信息

        Returns:
            WorkflowLog: 创建的工作流日志实体
        """
        workflow_log = WorkflowLog(
            workflow_id=workflow_id, workflow_name=workflow_name, trigger_info=json.dumps(trigger_info, ensure_ascii=False), status="started"
        )
        return self.create(workflow_log)

    def update_workflow_complete(self, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Optional[WorkflowLog]:
        """
        更新工作流完成状态

        Args:
            workflow_id: 工作流唯一标识
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[WorkflowLog]: 更新后的工作流日志实体
        """
        workflow_log = self.session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()
        if workflow_log:
            workflow_log.status = status
            workflow_log.result = json.dumps(result if result else {}, ensure_ascii=False)
            workflow_log.end_time = datetime.utcnow()
            self.session.commit()
            return workflow_log
        return None

    def get_workflow_logs(self, limit: int = 100, offset: int = 0) -> List[WorkflowLog]:
        """获取工作流日志列表"""
        return self.session.query(WorkflowLog).order_by(desc(WorkflowLog.start_time)).limit(limit).offset(offset).all()

    def get_workflow_log_by_id(self, workflow_id: str) -> Optional[WorkflowLog]:
        """根据工作流ID获取最新日志"""
        return self.session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()


class OperationLogRepository(Repository[OperationLog]):
    """操作日志仓库"""

    def __init__(self, session: Session):
        super().__init__(session, OperationLog)

    def create_operation_start(self, operation_id: str, workflow_id: str, operation_name: str, parameters: Dict[str, Any]) -> OperationLog:
        """
        记录操作开始

        Args:
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            operation_name: 操作名称
            parameters: 操作参数

        Returns:
            OperationLog: 创建的操作日志实体
        """
        # 获取最新的工作流日志ID
        workflow_log = self.session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()

        if not workflow_log:
            raise ValueError(f"找不到工作流日志记录: {workflow_id}")

        operation_log = OperationLog(
            operation_id=operation_id,
            workflow_log_id=workflow_log.id,
            operation_name=operation_name,
            parameters=json.dumps(parameters, ensure_ascii=False),
            status="started",
        )
        return self.create(operation_log)

    def update_operation_complete(
        self, operation_id: str, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> Optional[OperationLog]:
        """
        更新操作完成状态

        Args:
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[OperationLog]: 更新后的操作日志实体
        """
        operation_log = (
            self.session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()
        )

        if operation_log:
            operation_log.status = status
            operation_log.result = json.dumps(result if result else {}, ensure_ascii=False)
            operation_log.end_time = datetime.utcnow()
            self.session.commit()
            return operation_log
        return None

    def get_operations_for_workflow(self, workflow_id: str) -> List[OperationLog]:
        """获取指定工作流的所有操作日志"""
        workflow_log = self.session.query(WorkflowLog).filter(WorkflowLog.workflow_id == workflow_id).order_by(desc(WorkflowLog.start_time)).first()
        if workflow_log:
            return self.session.query(OperationLog).filter(OperationLog.workflow_log_id == workflow_log.id).all()
        return []


class TaskLogRepository(Repository[TaskLog]):
    """任务日志仓库"""

    def __init__(self, session: Session):
        super().__init__(session, TaskLog)

    def log_task_result(
        self, task_id: str, operation_id: str, workflow_id: str, task_name: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> TaskLog:
        """
        记录任务结果

        Args:
            task_id: 任务唯一标识
            operation_id: 关联的操作ID
            workflow_id: 关联的工作流ID
            task_name: 任务名称
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            TaskLog: 创建的任务日志实体
        """
        # 获取最新的操作日志ID
        operation_log = (
            self.session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()
        )

        if not operation_log:
            raise ValueError(f"找不到操作日志记录: {operation_id}")

        task_log = TaskLog(
            task_id=task_id,
            operation_log_id=operation_log.id,
            task_name=task_name,
            status=status,
            result=json.dumps(result if result else {}, ensure_ascii=False),
        )
        return self.create(task_log)

    def get_tasks_for_operation(self, operation_id: str) -> List[TaskLog]:
        """获取指定操作的所有任务日志"""
        operation_log = (
            self.session.query(OperationLog).filter(OperationLog.operation_id == operation_id).order_by(desc(OperationLog.start_time)).first()
        )
        if operation_log:
            return self.session.query(TaskLog).filter(TaskLog.operation_log_id == operation_log.id).all()
        return []


class PerformanceLogRepository(Repository[PerformanceLog]):
    """性能日志仓库"""

    def __init__(self, session: Session):
        super().__init__(session, PerformanceLog)

    def log_performance_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        context: Dict[str, Any],
        workflow_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> PerformanceLog:
        """
        记录性能指标

        Args:
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
        return self.create(performance_log)

    def get_metrics_by_name(self, metric_name: str, limit: int = 100) -> List[PerformanceLog]:
        """获取指定名称的性能指标"""
        return (
            self.session.query(PerformanceLog)
            .filter(PerformanceLog.metric_name == metric_name)
            .order_by(desc(PerformanceLog.created_at))
            .limit(limit)
            .all()
        )

    def get_metrics_for_workflow(self, workflow_id: str) -> List[PerformanceLog]:
        """获取指定工作流的所有性能指标"""
        return self.session.query(PerformanceLog).filter(PerformanceLog.workflow_id == workflow_id).order_by(desc(PerformanceLog.created_at)).all()


class ErrorLogRepository(Repository[ErrorLog]):
    """错误日志仓库"""

    def __init__(self, session: Session):
        super().__init__(session, ErrorLog)

    def log_error(
        self,
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
        return self.create(error_log)

    def get_recent_errors(self, limit: int = 50) -> List[ErrorLog]:
        """获取最近的错误日志"""
        return self.session.query(ErrorLog).order_by(desc(ErrorLog.created_at)).limit(limit).all()

    def get_errors_for_workflow(self, workflow_id: str) -> List[ErrorLog]:
        """获取指定工作流的所有错误日志"""
        return self.session.query(ErrorLog).filter(ErrorLog.workflow_id == workflow_id).order_by(desc(ErrorLog.created_at)).all()


class AuditLogRepository(Repository[AuditLog]):
    """审计日志仓库"""

    def __init__(self, session: Session):
        super().__init__(session, AuditLog)

    def log_audit(
        self, user_id: str, action: str, resource_type: str, resource_id: str, details: Dict[str, Any], workflow_id: Optional[str] = None
    ) -> AuditLog:
        """
        记录审计信息

        Args:
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
        return self.create(audit_log)

    def get_audit_logs_by_user(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """获取指定用户的所有审计日志"""
        return self.session.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(desc(AuditLog.created_at)).limit(limit).all()

    def get_audit_logs_by_resource(self, resource_type: str, resource_id: str) -> List[AuditLog]:
        """获取指定资源的所有审计日志"""
        return (
            self.session.query(AuditLog)
            .filter(AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id)
            .order_by(desc(AuditLog.created_at))
            .all()
        )
