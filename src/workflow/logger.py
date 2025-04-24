"""
工作流日志管理模块

提供工作流系统的日志管理功能，集成core.logger和flow_session的日志需求。
"""

import logging  # Added import
import os
from typing import Any, Dict, Optional

import yaml

# Removed import from src.core.logger
# from src.core.log_init import get_workflow_logger as get_core_workflow_logger # Renamed to avoid conflict # Removed this line


class WorkflowLogger:
    """工作流日志管理器"""

    _instance = None
    _loggers: Dict[str, logging.LoggerAdapter] = {}  # Use standard LoggerAdapter

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(WorkflowLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志管理器"""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._load_config()

    def _load_config(self):
        """加载日志配置"""
        config_path = os.path.join("config", "logging.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

    def get_logger(
        self, name: str, workflow_id: Optional[str] = None, session_id: Optional[str] = None, stage_id: Optional[str] = None
    ) -> logging.LoggerAdapter:
        """
        获取工作流日志记录器

        Args:
            name: 日志记录器名称
            workflow_id: 工作流ID
            session_id: 会话ID
            stage_id: 阶段ID

        Returns:
            logging.LoggerAdapter: 工作流日志适配器
        """
        logger_key = f"{name}:{workflow_id}:{session_id}:{stage_id}"

        if logger_key not in self._loggers:
            # Use standard logging.getLogger and create adapter manually
            logger = logging.getLogger(f"vibecopilot.workflow.{name}")  # Use a consistent base name

            # Add default context
            extra = {"workflow_id": "unknown", "session_id": "unknown", "stage_id": "unknown"}
            if workflow_id:
                extra["workflow_id"] = workflow_id
            if session_id:
                extra["session_id"] = session_id
            if stage_id:
                extra["stage_id"] = stage_id

            adapter = logging.LoggerAdapter(logger, extra)
            self._loggers[logger_key] = adapter

        return self._loggers[logger_key]

    def update_context(
        self, logger: logging.LoggerAdapter, workflow_id: Optional[str] = None, session_id: Optional[str] = None, stage_id: Optional[str] = None
    ):
        """
        更新日志上下文

        Args:
            logger: 要更新的日志适配器
            workflow_id: 新的工作流ID
            session_id: 新的会话ID
            stage_id: 新的阶段ID
        """
        if workflow_id is not None:
            logger.extra["workflow_id"] = workflow_id
        if session_id is not None:
            logger.extra["session_id"] = session_id
        if stage_id is not None:
            logger.extra["stage_id"] = stage_id


# 全局工作流日志管理器实例
workflow_logger = WorkflowLogger()
