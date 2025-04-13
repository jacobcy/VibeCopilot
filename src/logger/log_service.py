"""
日志服务模块

提供统一的日志服务，支持文件日志和数据库日志记录
"""

import datetime
import json
import logging
import os
import time
import traceback
from typing import Any, Dict, List, Optional, Union

from src.db.connection_manager import get_session_factory
from src.db.specific_managers.log_manager import LogManager

# 配置日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志文件路径 - 按日期命名
log_file = os.path.join(LOG_DIR, f"vibe-log-{datetime.datetime.now().strftime('%Y-%m-%d')}.log")

# 根据环境变量设置日志级别
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level, logging.INFO)

# 配置日志格式
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler() if log_level <= logging.INFO else logging.NullHandler()],
)

logger = logging.getLogger("vibe-log")

# 初始化日志管理器
try:
    session_factory = get_session_factory()
    session = session_factory()
    log_manager = LogManager(session)
except Exception as e:
    logger.error(f"初始化日志管理器失败: {e}")
    log_manager = None


def _log_entry(log_type: str, **kwargs) -> None:
    """
    创建并记录标准格式的日志条目到文件

    Args:
        log_type: 日志类型
        **kwargs: 日志数据
    """
    log_data = {"timestamp": datetime.datetime.now().isoformat(), "type": log_type, **kwargs}
    logger.info(json.dumps(log_data, ensure_ascii=False))


def log_workflow_start(workflow_id: str, workflow_name: str, trigger_info: Dict[str, Any]) -> None:
    """
    记录工作流开始

    Args:
        workflow_id: 工作流唯一标识
        workflow_name: 工作流名称
        trigger_info: 触发信息
    """
    # 文件日志
    _log_entry(log_type="workflow_start", workflow_id=workflow_id, workflow_name=workflow_name, trigger_info=trigger_info)

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_workflow_start(workflow_id, workflow_name, trigger_info)
        except Exception as e:
            logger.error(f"记录工作流开始到数据库失败: {e}")


def log_workflow_complete(workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
    """
    记录工作流完成

    Args:
        workflow_id: 工作流唯一标识
        status: 完成状态 (completed, failed, aborted)
        result: 结果数据
    """
    # 文件日志
    _log_entry(log_type="workflow_complete", workflow_id=workflow_id, status=status, result=result if result else {})

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_workflow_complete(workflow_id, status, result)
        except Exception as e:
            logger.error(f"记录工作流完成到数据库失败: {e}")


def log_operation_start(operation_id: str, workflow_id: str, operation_name: str, parameters: Dict[str, Any]) -> None:
    """
    记录操作开始

    Args:
        operation_id: 操作唯一标识
        workflow_id: 关联的工作流ID
        operation_name: 操作名称
        parameters: 操作参数
    """
    # 文件日志
    _log_entry(log_type="operation_start", operation_id=operation_id, workflow_id=workflow_id, operation_name=operation_name, parameters=parameters)

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_operation_start(operation_id, workflow_id, operation_name, parameters)
        except Exception as e:
            logger.error(f"记录操作开始到数据库失败: {e}")


def log_operation_complete(operation_id: str, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
    """
    记录操作完成

    Args:
        operation_id: 操作唯一标识
        workflow_id: 关联的工作流ID
        status: 完成状态 (completed, failed, aborted)
        result: 结果数据
    """
    # 文件日志
    _log_entry(log_type="operation_complete", operation_id=operation_id, workflow_id=workflow_id, status=status, result=result if result else {})

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_operation_complete(operation_id, workflow_id, status, result)
        except Exception as e:
            logger.error(f"记录操作完成到数据库失败: {e}")


def log_task_result(task_id: str, operation_id: str, workflow_id: str, task_name: str, status: str, result: Optional[Dict[str, Any]] = None) -> None:
    """
    记录任务结果

    Args:
        task_id: 任务唯一标识
        operation_id: 关联的操作ID
        workflow_id: 关联的工作流ID
        task_name: 任务名称
        status: 完成状态 (completed, failed, aborted)
        result: 结果数据
    """
    # 文件日志
    _log_entry(
        log_type="task_result",
        task_id=task_id,
        operation_id=operation_id,
        workflow_id=workflow_id,
        task_name=task_name,
        status=status,
        result=result if result else {},
    )

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_task_result(task_id, operation_id, workflow_id, task_name, status, result)
        except Exception as e:
            logger.error(f"记录任务结果到数据库失败: {e}")


def log_performance_metric(
    metric_name: str, value: Union[int, float], context: Dict[str, Any], workflow_id: Optional[str] = None, operation_id: Optional[str] = None
) -> None:
    """
    记录性能指标

    Args:
        metric_name: 指标名称
        value: 指标值
        context: 上下文信息
        workflow_id: 关联的工作流ID（可选）
        operation_id: 关联的操作ID（可选）
    """
    # 文件日志
    _log_entry(
        log_type="performance_metric", metric_name=metric_name, value=value, context=context, workflow_id=workflow_id, operation_id=operation_id
    )

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_performance_metric(metric_name, value, context, workflow_id, operation_id)
        except Exception as e:
            logger.error(f"记录性能指标到数据库失败: {e}")


def log_error(
    error_message: str,
    error_type: str,
    stack_trace: Optional[str] = None,
    workflow_id: Optional[str] = None,
    operation_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    记录错误

    Args:
        error_message: 错误消息
        error_type: 错误类型
        stack_trace: 堆栈跟踪（可选）
        workflow_id: 关联的工作流ID（可选）
        operation_id: 关联的操作ID（可选）
        context: 错误发生时的上下文信息（可选）
    """
    # 文件日志
    _log_entry(
        log_type="error",
        error_message=error_message,
        error_type=error_type,
        stack_trace=stack_trace,
        workflow_id=workflow_id,
        operation_id=operation_id,
        context=context if context else {},
    )

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_error(error_message, error_type, stack_trace, workflow_id, operation_id, context)
        except Exception as e:
            logger.error(f"记录错误到数据库失败: {e}")


def log_audit(user_id: str, action: str, resource_type: str, resource_id: str, details: Dict[str, Any], workflow_id: Optional[str] = None) -> None:
    """
    记录审计信息

    Args:
        user_id: 用户ID
        action: 执行的操作
        resource_type: 资源类型
        resource_id: 资源ID
        details: 详细信息
        workflow_id: 关联的工作流ID（可选）
    """
    # 文件日志
    _log_entry(
        log_type="audit",
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        workflow_id=workflow_id,
    )

    # 数据库日志
    if log_manager:
        try:
            log_manager.log_audit(user_id, action, resource_type, resource_id, details, workflow_id)
        except Exception as e:
            logger.error(f"记录审计信息到数据库失败: {e}")


# 查询日志数据的方法
def get_workflow_logs(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    获取工作流日志列表

    Args:
        limit: 限制返回数量
        offset: 偏移量

    Returns:
        List[Dict[str, Any]]: 日志列表
    """
    if log_manager:
        try:
            return log_manager.get_workflow_logs(limit, offset)
        except Exception as e:
            logger.error(f"获取工作流日志失败: {e}")
            return []
    return []


def get_workflow_operations(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的操作日志

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 操作日志列表
    """
    if log_manager:
        try:
            return log_manager.get_workflow_operations(workflow_id)
        except Exception as e:
            logger.error(f"获取工作流操作日志失败: {e}")
            return []
    return []


def get_operation_tasks(operation_id: str) -> List[Dict[str, Any]]:
    """
    获取操作的任务日志

    Args:
        operation_id: 操作ID

    Returns:
        List[Dict[str, Any]]: 任务日志列表
    """
    if log_manager:
        try:
            return log_manager.get_operation_tasks(operation_id)
        except Exception as e:
            logger.error(f"获取操作任务日志失败: {e}")
            return []
    return []


def get_recent_errors(limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取最近的错误日志

    Args:
        limit: 限制返回数量

    Returns:
        List[Dict[str, Any]]: 错误日志列表
    """
    if log_manager:
        try:
            return log_manager.get_recent_errors(limit)
        except Exception as e:
            logger.error(f"获取最近错误日志失败: {e}")
            return []
    return []


def get_user_audit_logs(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取用户的审计日志

    Args:
        user_id: 用户ID
        limit: 限制返回数量

    Returns:
        List[Dict[str, Any]]: 审计日志列表
    """
    if log_manager:
        try:
            return log_manager.get_user_audit_logs(user_id, limit)
        except Exception as e:
            logger.error(f"获取用户审计日志失败: {e}")
            return []
    return []
