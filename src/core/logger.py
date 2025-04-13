"""
日志工具模块

提供统一的日志配置和管理功能，包括通用日志和工作流专用日志。
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional


def setup_logger(name: str, level: Optional[int] = None, log_file: Optional[str] = None, format_str: Optional[str] = None) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（可选，如果不指定则使用root logger的级别）
        log_file: 日志文件路径（可选）
        format_str: 日志格式字符串（可选）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)

    # 只有在明确指定了level时才设置日志级别
    if level is not None:
        logger.setLevel(level)

    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger

    # 设置默认格式
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_str)

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取一个已配置的日志记录器，如果不存在则创建新的

    此函数不会修改日志级别，而是使用root logger的级别

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)

    # 如果日志记录器未配置，使用默认配置
    if not logger.handlers:
        # 设置默认日志文件
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # 使用日期作为日志文件名
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{date_str}.log")

        # 设置日志记录器，但不指定level，使用root logger的级别
        logger = setup_logger(name=name, log_file=log_file)

    return logger


class WorkflowLoggerAdapter(logging.LoggerAdapter):
    """
    工作流日志适配器

    为工作流相关日志添加上下文信息，如workflow_id, session_id等
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """处理日志消息，添加工作流上下文"""
        # 获取上下文信息
        workflow_id = self.extra.get("workflow_id", "unknown")
        session_id = self.extra.get("session_id", "unknown")
        stage_id = self.extra.get("stage_id", "unknown")

        # 格式化消息，添加上下文
        msg = f"[W:{workflow_id}|S:{session_id}|ST:{stage_id}] {msg}"
        return msg, kwargs


def setup_workflow_logger(
    name: str, workflow_id: Optional[str] = None, session_id: Optional[str] = None, stage_id: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    设置工作流专用日志记录器

    Args:
        name: 日志记录器名称
        workflow_id: 工作流ID
        session_id: 会话ID
        stage_id: 阶段ID

    Returns:
        logging.LoggerAdapter: 配置好的工作流日志适配器
    """
    # 确保工作流日志目录存在
    log_dir = os.path.join("logs", "workflow")
    os.makedirs(log_dir, exist_ok=True)

    # 设置日志文件路径
    log_file = os.path.join(log_dir, f"{name}.log")

    # 创建基础日志记录器
    logger = setup_logger(name=f"workflow.{name}", log_file=log_file, format_str="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 创建并返回适配器
    extra = {"workflow_id": workflow_id, "session_id": session_id, "stage_id": stage_id}

    return WorkflowLoggerAdapter(logger, extra)
