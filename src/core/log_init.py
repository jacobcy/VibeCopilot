"""
日志初始化模块

提供统一的日志配置管理，包括通用日志和工作流日志的初始化。
"""

import logging.config
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Removed imports from src.core.logger
# from src.workflow.logger import workflow_logger # Assuming this is still needed, otherwise remove


def init_logging(config_path: Optional[str] = None) -> None:
    """
    初始化日志系统

    Args:
        config_path: 日志配置文件路径，如果不指定则使用默认配置
    """
    # 创建日志目录
    _ensure_log_dirs()

    # 加载配置
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # 使用默认配置
        _setup_default_logging()


def _ensure_log_dirs() -> None:
    """确保所有需要的日志目录存在"""
    log_dirs = ["logs", "logs/workflow", "logs/workflow/session", "logs/workflow/stage", "logs/workflow/execution", "logs/workflow/error"]

    for dir_path in log_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def _setup_default_logging() -> None:
    """设置默认的日志配置"""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
            "workflow": {"format": "%(asctime)s [%(levelname)s] [%(name)s] [W:%(workflow_id)s|S:%(session_id)s|ST:%(stage_id)s] %(message)s"},
        },
        "handlers": {
            "workflow_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/workflow/workflow.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "workflow",
                "encoding": "utf8",
            },
            "session_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/workflow/session/session.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "workflow",
                "encoding": "utf8",
            },
            "stage_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/workflow/stage/stage.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "workflow",
                "encoding": "utf8",
            },
            "execution_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/workflow/execution/execution.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "workflow",
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/workflow/error/error.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "workflow",
                "level": "ERROR",
                "encoding": "utf8",
            },
        },
        "loggers": {
            "workflow": {"handlers": ["workflow_file", "error_file"], "level": "INFO", "propagate": False},
            "workflow.session": {"handlers": ["session_file", "error_file"], "level": "INFO", "propagate": False},
            "workflow.stage": {"handlers": ["stage_file", "error_file"], "level": "INFO", "propagate": False},
            "workflow.execution": {"handlers": ["execution_file", "error_file"], "level": "INFO", "propagate": False},
        },
    }

    logging.config.dictConfig(config)


def get_workflow_logger(module_name: str, **context: Any) -> logging.Logger:
    """
    获取工作流日志记录器

    Args:
        module_name: 模块名称
        context: 上下文信息，如workflow_id, session_id等

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(f"workflow.{module_name}")

    # 添加默认上下文
    extra = {"workflow_id": "unknown", "session_id": "unknown", "stage_id": "unknown"}
    extra.update(context)

    # Create adapter to add context
    # Ensure the logger itself is configured via dictConfig
    adapter = logging.LoggerAdapter(logger, extra)
    return adapter


def get_logger(name: str) -> logging.Logger:
    """
    获取一个日志记录器。

    日志记录器的配置应通过 init_logging 完成。
    此函数仅用于获取已配置或将由根记录器配置处理的记录器实例。

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    # Configuration is handled by init_logging using dictConfig.
    # This function simply returns the logger instance.
    return logging.getLogger(name)
