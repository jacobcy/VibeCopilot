"""Status模块状态查询API

为Health模块提供一个查询Status状态的简单API，避免直接依赖。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 强制禁用状态模块集成
_status_module_available = False


def _check_status_module_available() -> bool:
    """检查Status模块是否可用

    Returns:
        bool: Status模块是否可用
    """
    # 强制返回False，暂时禁用与Status模块的所有交互
    return False


def get_status_health(domain: Optional[str] = None) -> Dict[str, Any]:
    """获取状态模块的健康信息

    Args:
        domain: 可选，特定领域的状态

    Returns:
        Dict[str, Any]: 状态健康信息
    """
    # 直接返回空数据，不尝试检查状态
    logger.info("状态API已禁用，不进行状态健康检查")
    return {"disabled": True, "message": "状态检查已禁用"}


def _get_mock_status_health(domain: Optional[str] = None) -> Dict[str, Any]:
    """获取模拟的状态健康信息，用于Status模块不可用时

    Args:
        domain: 可选，特定领域的状态

    Returns:
        Dict[str, Any]: 模拟的状态健康信息
    """
    # 此函数已不再使用，但保留以便将来恢复功能
    return {"disabled": True}


def _process_status_data(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理状态数据，提取健康相关信息

    Args:
        status_data: 状态数据

    Returns:
        Dict[str, Any]: 健康相关信息
    """
    # 此函数已不再使用，但保留以便将来恢复功能
    return {"disabled": True}


def _process_system_status(system_status: Dict[str, Any]) -> Dict[str, Any]:
    """处理系统状态数据，提取健康相关信息

    Args:
        system_status: 系统状态数据

    Returns:
        Dict[str, Any]: 系统健康信息
    """
    # 此函数已不再使用，但保留以便将来恢复功能
    return {"disabled": True}
