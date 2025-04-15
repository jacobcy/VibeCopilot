"""
日志管理器

提供对日志数据的统一管理，整合多种日志仓库
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from src.db.repositories.log_repository import (
    AuditLogRepository,
    ErrorLogRepository,
    OperationLogRepository,
    PerformanceLogRepository,
    TaskLogRepository,
    WorkflowLogRepository,
)
from src.models.db.log import AuditLog, ErrorLog, OperationLog, PerformanceLog, TaskLog, WorkflowLog


class LogManager:
    """日志管理器，整合多种日志仓库提供统一的日志管理接口"""

    def __init__(self, session: Session):
        """
        初始化日志管理器

        Args:
            session: 数据库会话
        """
        self.session = session
        self.workflow_log_repo = WorkflowLogRepository(session)
        self.operation_log_repo = OperationLogRepository(session)
        self.task_log_repo = TaskLogRepository(session)
        self.performance_log_repo = PerformanceLogRepository(session)
        self.error_log_repo = ErrorLogRepository(session)
        self.audit_log_repo = AuditLogRepository(session)

    # 工作流日志方法
    def log_workflow_start(self, workflow_id: str, workflow_name: str, trigger_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录工作流开始

        Args:
            workflow_id: 工作流唯一标识
            workflow_name: 工作流名称
            trigger_info: 触发信息

        Returns:
            Dict[str, Any]: 创建的工作流日志实体字典
        """
        workflow_log = self.workflow_log_repo.create_workflow_start(workflow_id, workflow_name, trigger_info)
        return workflow_log.to_dict()

    def log_workflow_complete(self, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        记录工作流完成

        Args:
            workflow_id: 工作流唯一标识
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[Dict[str, Any]]: 更新后的工作流日志实体字典
        """
        workflow_log = self.workflow_log_repo.update_workflow_complete(workflow_id, status, result)
        return workflow_log.to_dict() if workflow_log else None

    def get_workflow_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取工作流日志列表"""
        logs = self.workflow_log_repo.get_workflow_logs(limit, offset)
        return [log.to_dict() for log in logs]

    def get_workflow_log(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取指定工作流的日志"""
        log = self.workflow_log_repo.get_workflow_log_by_id(workflow_id)
        return log.to_dict() if log else None

    # 操作日志方法
    def log_operation_start(self, operation_id: str, workflow_id: str, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录操作开始

        Args:
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            operation_name: 操作名称
            parameters: 操作参数

        Returns:
            Dict[str, Any]: 创建的操作日志实体字典
        """
        operation_log = self.operation_log_repo.create_operation_start(operation_id, workflow_id, operation_name, parameters)
        return operation_log.to_dict()

    def log_operation_complete(
        self, operation_id: str, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        记录操作完成

        Args:
            operation_id: 操作唯一标识
            workflow_id: 关联的工作流ID
            status: 完成状态 (completed, failed, aborted)
            result: 结果数据

        Returns:
            Optional[Dict[str, Any]]: 更新后的操作日志实体字典
        """
        operation_log = self.operation_log_repo.update_operation_complete(operation_id, workflow_id, status, result)
        return operation_log.to_dict() if operation_log else None

    def get_workflow_operations(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有操作日志"""
        operations = self.operation_log_repo.get_operations_for_workflow(workflow_id)
        return [op.to_dict() for op in operations]

    # 任务日志方法
    def log_task_result(
        self, task_id: str, operation_id: str, workflow_id: str, task_name: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
            Dict[str, Any]: 创建的任务日志实体字典
        """
        task_log = self.task_log_repo.log_task_result(task_id, operation_id, workflow_id, task_name, status, result)
        return task_log.to_dict()

    def get_operation_tasks(self, operation_id: str) -> List[Dict[str, Any]]:
        """获取指定操作的所有任务日志"""
        tasks = self.task_log_repo.get_tasks_for_operation(operation_id)
        return [task.to_dict() for task in tasks]

    # 性能日志方法
    def log_performance_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        context: Dict[str, Any],
        workflow_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        记录性能指标

        Args:
            metric_name: 指标名称
            value: 指标值
            context: 上下文信息
            workflow_id: 关联的工作流ID（可选）
            operation_id: 关联的操作ID（可选）

        Returns:
            Dict[str, Any]: 创建的性能日志实体字典
        """
        performance_log = self.performance_log_repo.log_performance_metric(metric_name, value, context, workflow_id, operation_id)
        return performance_log.to_dict()

    def get_metrics_by_name(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指定名称的性能指标"""
        metrics = self.performance_log_repo.get_metrics_by_name(metric_name, limit)
        return [metric.to_dict() for metric in metrics]

    # 错误日志方法
    def log_error(
        self,
        error_message: str,
        error_type: str,
        stack_trace: Optional[str] = None,
        workflow_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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
            Dict[str, Any]: 创建的错误日志实体字典
        """
        error_log = self.error_log_repo.log_error(error_message, error_type, stack_trace, workflow_id, operation_id, context)
        return error_log.to_dict()

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误日志"""
        errors = self.error_log_repo.get_recent_errors(limit)
        return [error.to_dict() for error in errors]

    # 审计日志方法
    def log_audit(
        self, user_id: str, action: str, resource_type: str, resource_id: str, details: Dict[str, Any], workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
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
            Dict[str, Any]: 创建的审计日志实体字典
        """
        audit_log = self.audit_log_repo.log_audit(user_id, action, resource_type, resource_id, details, workflow_id)
        return audit_log.to_dict()

    def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指定用户的审计日志"""
        logs = self.audit_log_repo.get_audit_logs_by_user(user_id, limit)
        return [log.to_dict() for log in logs]
