#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流基础操作

提供工作流的基本工具函数。
"""

import logging
import os

from src.core.config import get_config

logger = logging.getLogger(__name__)


def get_workflows_directory() -> str:
    """获取工作流目录路径"""
    config = get_config()
    # 优先使用环境变量中的工作流目录
    workflows_dir = os.environ.get("VIBECOPILOT_WORKFLOW_DIR")
    if not workflows_dir:
        # 否则使用配置中的数据目录下的 workflows 子目录
        data_dir = config.get("paths.data_dir", "data")
        if not os.path.isabs(data_dir):
            # 如果是相对路径，转换为绝对路径
            data_dir = os.path.abspath(data_dir)
        workflows_dir = os.path.join(data_dir, "workflows")

    ensure_directory_exists(workflows_dir)
    return workflows_dir


def get_workflow_file_path(workflow_id: str) -> str:
    """
    获取工作流文件的完整路径

    Args:
        workflow_id: 工作流ID

    Returns:
        str: 工作流文件的完整路径
    """
    workflows_dir = get_workflows_directory()
    return os.path.join(workflows_dir, f"{workflow_id}.json")


def ensure_directory_exists(directory_path: str) -> None:
    """
    确保目录存在，如果不存在则创建

    Args:
        directory_path: 目录路径
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        logger.debug(f"创建目录: {directory_path}")
