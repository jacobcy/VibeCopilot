#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块配置管理

提供日志模块的配置加载和管理功能。
"""

import os
from typing import Any, Dict

from src.core.config import get_config as get_core_config


def get_default_config() -> Dict[str, Any]:
    """
    获取默认日志配置

    Returns:
        Dict[str, Any]: 默认配置字典
    """
    core_config = get_core_config()

    # 获取数据目录
    data_dir = core_config.get("paths.data_dir", "data")
    if not os.path.isabs(data_dir):
        # 如果是相对路径，转换为绝对路径
        data_dir = os.path.abspath(data_dir)

    # 默认日志配置
    return {
        "storage_type": "file",  # 'file' 或 'database'
        "log_dir": os.path.join(data_dir, "logs"),
        "workflow_execution_dir": os.path.join(data_dir, "logs", "workflow_executions"),
        "workflow_operation_dir": os.path.join(data_dir, "logs", "workflow_operations"),
        "max_log_entries": 1000,
        "enable_operation_logging": True,
        "enable_execution_logging": True,
        "log_retention_days": 90,  # 日志保留天数
    }


def get_config() -> Dict[str, Any]:
    """
    获取日志模块配置，合并默认配置和用户配置

    Returns:
        Dict[str, Any]: 配置字典
    """
    # 获取默认配置
    config = get_default_config()

    # 获取核心配置
    core_config = get_core_config()

    # 合并日志特定配置
    if "log" in core_config:
        for key, value in core_config["log"].items():
            config[key] = value

    # 确保日志目录存在
    os.makedirs(config["log_dir"], exist_ok=True)
    os.makedirs(config["workflow_execution_dir"], exist_ok=True)
    os.makedirs(config["workflow_operation_dir"], exist_ok=True)

    return config
