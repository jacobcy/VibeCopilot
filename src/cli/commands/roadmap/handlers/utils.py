"""
路线图命令相关工具函数

提供路线图状态计算、格式化和其他辅助功能。
"""

from typing import Dict, List, Union


def count_status(items: List[Dict]) -> Dict[str, Union[int, float]]:
    """统计项目状态分布

    Args:
        items: 项目列表

    Returns:
        状态统计结果，包含各状态数量和百分比
    """
    if not items:
        return {"total": 0, "status_counts": {}, "percentages": {}}

    total = len(items)
    status_counts = {}

    # 统计各状态数量
    for item in items:
        status = item.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1

    # 计算百分比
    percentages = {}
    for status, count in status_counts.items():
        percentages[status] = round((count / total) * 100, 2)

    return {"total": total, "status_counts": status_counts, "percentages": percentages}
