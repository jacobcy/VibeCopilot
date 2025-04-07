"""
工作流配置模块

提供工作流系统的配置参数和管理函数
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parents[3]

# 工作流模板目录
TEMPLATE_DIR = os.environ.get("VIBECOPILOT_TEMPLATE_DIR", str(PROJECT_ROOT / "templates" / "flow"))

# 模板文件扩展名
TEMPLATE_EXTENSION = ".json"

# 工作流配置
WORKFLOW_CONFIG = {"templates_dir": TEMPLATE_DIR, "template_extension": TEMPLATE_EXTENSION}


def get_template_path(template_name: str) -> str:
    """
    获取模板文件的完整路径

    Args:
        template_name: 模板名称

    Returns:
        模板文件的完整路径
    """
    if not template_name.endswith(TEMPLATE_EXTENSION):
        template_name += TEMPLATE_EXTENSION

    return os.path.join(TEMPLATE_DIR, template_name)


def list_templates() -> list:
    """
    列出所有可用的工作流模板

    Returns:
        模板名称列表
    """
    if not os.path.exists(TEMPLATE_DIR):
        return []

    templates = []
    for file in os.listdir(TEMPLATE_DIR):
        if file.endswith(TEMPLATE_EXTENSION):
            templates.append(file.replace(TEMPLATE_EXTENSION, ""))

    return templates
