"""
规则命令工具函数

提供规则命令相关的工具函数。
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def validate_single_rule(rule) -> bool:
    """验证单个规则

    Args:
        rule: 规则对象

    Returns:
        验证结果
    """
    try:
        # 基本验证
        if not rule.id or not rule.name:
            logger.error("规则缺少必要属性")
            return False

        # 内容验证
        if not rule.content:
            logger.error("规则内容为空")
            return False

        return True
    except Exception as e:
        logger.error("验证规则失败: %s", str(e))
        return False


def get_template(template_manager, template_type: str) -> Optional[Any]:
    """获取模板

    Args:
        template_manager: 模板管理器
        template_type: 模板类型

    Returns:
        模板对象
    """
    try:
        return template_manager.get_template(template_type)
    except Exception as e:
        logger.error("获取模板失败: %s", str(e))
        return None


def prepare_variables(args) -> Optional[Dict[str, Any]]:
    """准备变量

    Args:
        args: 命令参数

    Returns:
        变量字典
    """
    try:
        variables = {}

        # 从args中获取变量
        if isinstance(args, dict):
            variables.update(args)
        else:
            # 将args对象转换为字典
            variables.update(vars(args))

        return variables
    except Exception as e:
        logger.error("准备变量失败: %s", str(e))
        return None
