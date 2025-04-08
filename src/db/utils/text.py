"""
文本处理工具模块

提供文本处理相关的工具函数。
"""

import re
from typing import Optional


def normalize_string(text: str, max_length: Optional[int] = 50) -> str:
    """
    将字符串标准化为可用作标识符的形式

    Args:
        text: 需要标准化的字符串
        max_length: 结果的最大长度，默认50

    Returns:
        标准化后的字符串
    """
    if not text:
        return ""

    # 将文本转换为小写
    text = text.lower()

    # 将空格和特殊字符替换为下划线
    text = re.sub(r"[\s\-]+", "_", text)

    # 移除所有非字母数字和下划线的字符
    text = re.sub(r"[^\w]", "", text)

    # 确保不以数字开头（如果以数字开头，加上前缀）
    if text and text[0].isdigit():
        text = f"r_{text}"

    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度，并添加后缀

    Args:
        text: 需要截断的文本
        max_length: 结果的最大长度，默认100
        suffix: 截断后添加的后缀，默认为"..."

    Returns:
        截断后的文本
    """
    if not text or len(text) <= max_length:
        return text

    # 计算实际截断位置
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        truncate_at = max_length
        suffix = ""

    return text[:truncate_at] + suffix
