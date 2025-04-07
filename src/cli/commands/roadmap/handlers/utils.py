"""
路线图管理命令工具函数

提供路线图管理所需的通用工具函数。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def count_status(items: List[Dict]) -> Dict[str, int]:
    """统计不同状态的数量

    Args:
        items: 要统计的项目列表

    Returns:
        包含各状态数量的字典
    """
    stats = {}
    for item in items:
        status = item.get("status", "unknown")
        if status not in stats:
            stats[status] = 0
        stats[status] += 1
    stats["total"] = len(items)
    return stats
