"""
日志初始化模块

提供统一的日志配置管理，包括通用日志和工作流日志的初始化。
"""

import logging.config
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.logger import setup_logger, setup_workflow_logger
from src.workflow.logger import workflow_logger


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
            "workflow": {"format": "%(asctime)s [%(levelname)s] [%(workflow_id)s] %(name)s: %(message)s"},
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

    # 创建适配器添加上下文
    logger = logging.LoggerAdapter(logger, extra)

    return logger


def get_logger(name: str, is_workflow: bool = False) -> logging.Logger:
    """
    获取日志记录器的统一接口

    Args:
        name: 日志记录器名称
        is_workflow: 是否是工作流日志

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if is_workflow:
        return workflow_logger.get_logger(name)
    else:
        return setup_logger(name)
