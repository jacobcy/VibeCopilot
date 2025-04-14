"""
工作流配置模块

提供工作流系统的配置参数和管理函数
"""

import os
from pathlib import Path

from src.core.config.manager import get_config


def get_template_path(template_name: str) -> str:
    """
    获取模板文件的完整路径

    Args:
        template_name: 模板名称

    Returns:
        模板文件的完整路径
    """
    config = get_config()
    template_extension = config.get("workflow.template_extension")
    templates_dir = config.get("workflow.templates_dir")

    if not template_name.endswith(template_extension):
        template_name += template_extension

    return os.path.join(templates_dir, template_name)


def list_templates() -> list:
    """
    列出所有可用的工作流模板

    Returns:
        模板名称列表
    """
    config = get_config()
    template_extension = config.get("workflow.template_extension")
    templates_dir = config.get("workflow.templates_dir")

    if not os.path.exists(templates_dir):
        return []

    templates = []
    for file in os.listdir(templates_dir):
        if file.endswith(template_extension):
            templates.append(file.replace(template_extension, ""))

    return templates


def get_workflows_directory() -> str:
    """
    获取工作流文件存储目录

    Returns:
        工作流文件存储目录的路径
    """
    config = get_config()
    return config.get("workflow.workflows_dir")
