"""
文档引擎类型定义

提供文档引擎使用的枚举类型和自定义类型
"""

from enum import Enum


class LinkType(Enum):
    """链接类型"""

    DIRECT = "direct"  # 直接链接
    REFERENCE = "reference"  # 引用链接
    BACKLINK = "backlink"  # 反向链接
