"""
路线图数据验证模块

提供对路线图数据的验证功能。
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def validate_roadmap_data(data: Dict[str, Any]) -> bool:
    """
    验证路线图数据是否有效

    Args:
        data: 路线图数据

    Returns:
        bool: 数据是否有效

    Raises:
        ValueError: 如果数据无效
    """
    # 验证基本结构
    if not isinstance(data, dict):
        raise ValueError("路线图数据必须是字典类型")

    # 验证必填字段
    if "title" not in data:
        raise ValueError("路线图必须包含标题")

    # 验证里程碑
    if "milestones" in data:
        _validate_milestones(data["milestones"])

    # 验证任务
    if "tasks" in data:
        _validate_tasks(data["tasks"])

    # 如果所有验证都通过，则返回True
    return True


def _validate_milestones(milestones: Any) -> None:
    """验证里程碑数据"""
    if not isinstance(milestones, list):
        raise ValueError("milestones必须是列表类型")

    for i, milestone in enumerate(milestones):
        if not isinstance(milestone, dict):
            raise ValueError(f"milestone #{i}必须是字典类型")

        # 验证里程碑ID
        if "id" in milestone and not _is_valid_id(milestone["id"]):
            raise ValueError(f"milestone #{i}的ID '{milestone['id']}'无效")

        # 验证里程碑名称
        if "name" not in milestone:
            raise ValueError(f"milestone #{i}缺少name字段")

        # 验证日期
        _validate_dates(milestone, i, "milestone")

        # 验证进度
        if "progress" in milestone:
            _validate_progress(milestone["progress"], i, "milestone")


def _validate_tasks(tasks: Any) -> None:
    """验证任务数据"""
    if not isinstance(tasks, list):
        raise ValueError("tasks必须是列表类型")

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"task #{i}必须是字典类型")

        # 验证任务ID
        if "id" in task and not _is_valid_id(task["id"]):
            raise ValueError(f"task #{i}的ID '{task['id']}'无效")

        # 验证任务标题
        if "title" not in task:
            raise ValueError(f"task #{i}缺少title字段")

        # 验证里程碑引用
        if "milestone" in task and not _is_valid_reference(task["milestone"]):
            raise ValueError(f"task #{i}的milestone '{task['milestone']}'无效")

        # 验证日期
        _validate_dates(task, i, "task")

        # 验证状态
        _validate_status(task, i)


def _is_valid_id(id_str: str) -> bool:
    """验证ID是否有效"""
    if not isinstance(id_str, str):
        return False

    # ID应该只包含字母、数字、连字符和下划线
    return bool(re.match(r"^[a-zA-Z0-9\-_]+$", id_str))


def _is_valid_reference(ref_str: str) -> bool:
    """验证引用是否有效"""
    if not isinstance(ref_str, str):
        return False

    # 引用应该只包含字母、数字、连字符和下划线
    return bool(re.match(r"^[a-zA-Z0-9\-_]+$", ref_str))


def _validate_dates(item: Dict[str, Any], index: int, item_type: str) -> None:
    """验证日期字段"""
    # 验证开始日期
    if "start_date" in item:
        start_date = item["start_date"]
        if not _is_valid_date(start_date):
            raise ValueError(f"{item_type} #{index}的start_date '{start_date}'格式无效")

    # 验证结束日期
    if "end_date" in item:
        end_date = item["end_date"]
        if not _is_valid_date(end_date):
            raise ValueError(f"{item_type} #{index}的end_date '{end_date}'格式无效")

    # 验证截止日期
    if "due_date" in item:
        due_date = item["due_date"]
        if not _is_valid_date(due_date):
            raise ValueError(f"{item_type} #{index}的due_date '{due_date}'格式无效")

    # 验证日期顺序
    if "start_date" in item and "end_date" in item:
        start = _parse_date(item["start_date"])
        end = _parse_date(item["end_date"])
        if start and end and start > end:
            raise ValueError(f"{item_type} #{index}的start_date晚于end_date")


def _is_valid_date(date_str: Any) -> bool:
    """检查日期字符串是否有效"""
    if not date_str:  # 允许空日期
        return True

    if isinstance(date_str, datetime):
        return True

    if not isinstance(date_str, str):
        return False

    # 尝试解析日期
    return _parse_date(date_str) is not None


def _parse_date(date_str: str) -> Optional[datetime]:
    """尝试解析日期字符串"""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def _validate_progress(progress: Any, index: int, item_type: str) -> None:
    """验证进度值"""
    try:
        progress = float(progress)
        if progress < 0 or progress > 100:
            raise ValueError(f"{item_type} #{index}的progress必须在0-100之间")
    except (ValueError, TypeError):
        raise ValueError(f"{item_type} #{index}的progress '{progress}'必须是数字")


def _validate_status(task: Dict[str, Any], index: int) -> None:
    """验证任务状态"""
    if "status" not in task:
        return  # 状态是可选的

    status = task["status"]

    # 这个列表可以根据实际需求调整
    valid_statuses = [
        "todo",
        "in_progress",
        "review",
        "completed",
        "blocked",
        "backlog",
        "doing",
        "done",
    ]

    if status not in valid_statuses:
        raise ValueError(f"task #{index}的status '{status}'无效，有效值为: {', '.join(valid_statuses)}")
