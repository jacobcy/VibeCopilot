#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间处理工具

提供处理记忆服务时间的工具函数，包括时间戳生成、格式转换和时间解析等。
"""

import datetime
import re
import time
from typing import Optional, Tuple, Union

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

# 常量定义
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"  # ISO 8601 格式
DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"  # 显示格式
DATE_FORMAT = "%Y-%m-%d"  # 日期格式

# 时间单位正则表达式
TIME_UNIT_PATTERN = re.compile(r"(\d+)([dhwmy])")

# 时间单位映射
TIME_UNITS = {"d": "days", "h": "hours", "w": "weeks", "m": "months", "y": "years"}

# 自然语言时间表达式
NATURAL_TIME_EXPRESSIONS = {
    "today": lambda: datetime.datetime.now(),
    "yesterday": lambda: datetime.datetime.now() - datetime.timedelta(days=1),
    "last week": lambda: datetime.datetime.now() - datetime.timedelta(weeks=1),
    "last month": lambda: datetime.datetime.now() - relativedelta(months=1),
    "last year": lambda: datetime.datetime.now() - relativedelta(years=1),
    "this week": lambda: datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday()),
    "this month": lambda: datetime.datetime.now().replace(day=1),
    "this year": lambda: datetime.datetime.now().replace(month=1, day=1),
}


def get_current_timestamp() -> float:
    """
    获取当前时间戳。

    Returns:
        当前时间戳（秒）
    """
    return time.time()


def get_current_datetime() -> datetime.datetime:
    """
    获取当前的datetime对象。

    Returns:
        当前datetime对象
    """
    return datetime.datetime.now()


def timestamp_to_datetime(timestamp: float) -> datetime.datetime:
    """
    将时间戳转换为datetime对象。

    Args:
        timestamp: 时间戳（秒）

    Returns:
        datetime对象
    """
    return datetime.datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt: datetime.datetime) -> float:
    """
    将datetime对象转换为时间戳。

    Args:
        dt: datetime对象

    Returns:
        时间戳（秒）
    """
    return dt.timestamp()


def format_datetime(dt: datetime.datetime, format_str: str = DISPLAY_FORMAT) -> str:
    """
    将datetime对象格式化为字符串。

    Args:
        dt: datetime对象
        format_str: 格式字符串，默认为DISPLAY_FORMAT

    Returns:
        格式化后的字符串
    """
    return dt.strftime(format_str)


def parse_datetime(datetime_str: str) -> Optional[datetime.datetime]:
    """
    解析日期时间字符串为datetime对象。

    Args:
        datetime_str: 日期时间字符串

    Returns:
        datetime对象，如果解析失败则返回None
    """
    try:
        return date_parser.parse(datetime_str)
    except Exception:
        return None


def parse_timeframe(timeframe: str) -> Optional[datetime.datetime]:
    """
    解析时间范围字符串为datetime对象。

    支持的格式:
    - 自然语言: 'today', 'yesterday', 'last week', 'last month', 'last year'
    - 简写格式: '7d', '24h', '2w', '3m', '1y'
    - 标准日期: 'YYYY-MM-DD'

    Args:
        timeframe: 时间范围字符串

    Returns:
        表示时间范围开始的datetime对象，如果解析失败则返回None
    """
    if not timeframe:
        # 默认为7天前
        return datetime.datetime.now() - datetime.timedelta(days=7)

    # 检查是否是自然语言表达式
    if timeframe.lower() in NATURAL_TIME_EXPRESSIONS:
        return NATURAL_TIME_EXPRESSIONS[timeframe.lower()]()

    # 检查是否是简写格式
    match = TIME_UNIT_PATTERN.match(timeframe)
    if match:
        value, unit = match.groups()
        if unit in TIME_UNITS:
            delta_args = {TIME_UNITS[unit]: int(value)}
            if unit in ["m", "y"]:
                return datetime.datetime.now() - relativedelta(**delta_args)
            else:
                return datetime.datetime.now() - datetime.timedelta(**delta_args)

    # 尝试标准日期解析
    try:
        dt = parse_datetime(timeframe)
        if dt:
            return dt
    except Exception:
        pass

    # 无法解析，返回默认值（7天前）
    return datetime.datetime.now() - datetime.timedelta(days=7)


def get_date_range(timeframe: str) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    获取时间范围的起止时间。

    Args:
        timeframe: 时间范围字符串

    Returns:
        (开始时间, 结束时间)元组
    """
    start_time = parse_timeframe(timeframe)
    end_time = datetime.datetime.now()

    return start_time, end_time


def calculate_time_difference(start_time: Union[float, datetime.datetime], end_time: Union[float, datetime.datetime] = None) -> float:
    """
    计算两个时间点之间的差异（秒数）。

    Args:
        start_time: 开始时间点（时间戳或datetime对象）
        end_time: 结束时间点（时间戳或datetime对象），如果为None则使用当前时间

    Returns:
        时间差异（秒）
    """
    # 如果未提供结束时间，使用当前时间
    if end_time is None:
        end_time = get_current_timestamp()

    # 将datetime对象转换为时间戳
    if isinstance(start_time, datetime.datetime):
        start_time = datetime_to_timestamp(start_time)

    if isinstance(end_time, datetime.datetime):
        end_time = datetime_to_timestamp(end_time)

    # 计算差异
    return end_time - start_time


def format_time_difference(seconds: float) -> str:
    """
    将时间差异（秒）格式化为可读字符串。

    Args:
        seconds: 时间差异（秒）

    Returns:
        格式化后的字符串，例如："2小时前", "3天前"
    """
    if seconds < 60:
        return f"{int(seconds)}秒前"
    elif seconds < 3600:
        return f"{int(seconds / 60)}分钟前"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}小时前"
    elif seconds < 604800:
        return f"{int(seconds / 86400)}天前"
    elif seconds < 2592000:
        return f"{int(seconds / 604800)}周前"
    elif seconds < 31536000:
        return f"{int(seconds / 2592000)}个月前"
    else:
        return f"{int(seconds / 31536000)}年前"


def is_same_day(dt1: datetime.datetime, dt2: datetime.datetime) -> bool:
    """
    检查两个datetime对象是否在同一天。

    Args:
        dt1: 第一个datetime对象
        dt2: 第二个datetime对象

    Returns:
        如果在同一天则返回True，否则返回False
    """
    return dt1.year == dt2.year and dt1.month == dt2.month and dt1.day == dt2.day


def get_day_start(dt: datetime.datetime) -> datetime.datetime:
    """
    获取给定日期的开始时间（00:00:00）。

    Args:
        dt: 源datetime对象

    Returns:
        该日期的开始时间
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(dt: datetime.datetime) -> datetime.datetime:
    """
    获取给定日期的结束时间（23:59:59.999999）。

    Args:
        dt: 源datetime对象

    Returns:
        该日期的结束时间
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
