#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub项目分析日期工具模块.

提供通用的日期解析和处理功能。
"""

import datetime
from typing import Optional


def parse_date(date_str: str) -> datetime.datetime:
    """解析日期字符串.

    Args:
        date_str: 日期字符串

    Returns:
        datetime.datetime: 日期对象，如解析失败则返回当前日期
    """
    if not date_str:
        return datetime.datetime.now(datetime.timezone.utc)

    try:
        return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        # 尝试其他格式
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc
            )
        except ValueError:
            # 回退到当前日期
            return datetime.datetime.now(datetime.timezone.utc)


def format_date(date_obj: datetime.datetime, format_str: str = "%Y-%m-%d") -> str:
    """将日期对象格式化为字符串.

    Args:
        date_obj: 日期对象
        format_str: 日期格式字符串

    Returns:
        str: 格式化后的日期字符串
    """
    return date_obj.strftime(format_str)


def get_days_difference(start_date: datetime.datetime, end_date: datetime.datetime) -> int:
    """计算两个日期之间的天数差.

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        int: 天数差
    """
    return (end_date - start_date).days


def is_date_passed(date_obj: datetime.datetime) -> bool:
    """检查日期是否已过期.

    Args:
        date_obj: 要检查的日期

    Returns:
        bool: 如果日期已过期则返回True
    """
    return date_obj < datetime.datetime.now(datetime.timezone.utc)
