"""
内容类型检测模块

提供内容类型自动检测功能
"""

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


def detect_content_type(file_path: str) -> str:
    """检测内容类型

    Args:
        file_path: 文件路径

    Returns:
        str: 内容类型 ("rule", "document", "generic")
    """
    # 基于文件路径判断内容类型
    lower_path = file_path.lower()

    # 如果在rules目录中，或者以rule.mdc结尾，则为规则
    if (
        "rules/" in lower_path
        or lower_path.endswith("rule.mdc")
        or lower_path.endswith("rule.md")
        or "cmd-rules" in lower_path
        or "core-rules" in lower_path
        or "flow-rules" in lower_path
        or "role-rules" in lower_path
        or "tech-rules" in lower_path
    ):
        return "rule"

    # 如果在docs目录中，则为文档
    if "docs/" in lower_path or "documents/" in lower_path or "/doc/" in lower_path or lower_path.endswith(".md") or lower_path.endswith(".mdx"):
        return "document"

    # 否则为通用内容
    return "generic"


def detect_content_type_from_text(content: str, context: str = "") -> str:
    """从内容文本检测内容类型

    Args:
        content: 文本内容
        context: 上下文信息(文件路径等)

    Returns:
        str: 内容类型 ("rule", "document", "generic")
    """
    # 如果有上下文，优先使用上下文判断
    if context:
        return detect_content_type(context)

    # 从内容判断
    # 检测是否为规则
    if _is_rule_content(content):
        return "rule"

    # 检测是否为文档
    if _is_document_content(content):
        return "document"

    # 默认为通用内容
    return "generic"


def _is_rule_content(content: str) -> bool:
    """判断内容是否为规则

    Args:
        content: 文本内容

    Returns:
        bool: 是否为规则
    """
    # 规则内容通常有Front Matter和规则特定的标记
    if re.search(r"^---\s*\n.*\n---\s*\n", content, re.DOTALL):
        # 存在Front Matter，检查是否包含规则关键词
        rule_keywords = [
            "rule",
            "规则",
            "约定",
            "convention",
            "standard",
            "应用条件",
            "应用场景",
            "适用条件",
            "适用场景",
        ]

        for keyword in rule_keywords:
            if keyword.lower() in content.lower():
                return True

    return False


def _is_document_content(content: str) -> bool:
    """判断内容是否为文档

    Args:
        content: 文本内容

    Returns:
        bool: 是否为文档
    """
    # 文档通常有标题结构
    heading_pattern = r"^#{1,6}\s+.+$"
    if re.search(heading_pattern, content, re.MULTILINE):
        return True

    # 检查是否有典型的文档结构（多个标题、列表等）
    doc_indicators = 0

    # 检查标题
    if re.search(r"^#{1,6}\s+.+$", content, re.MULTILINE):
        doc_indicators += 1

    # 检查列表
    if re.search(r"^(\s*[-*+]|\d+\.)\s+.+$", content, re.MULTILINE):
        doc_indicators += 1

    # 检查代码块
    if re.search(r"```[\w]*\n.*?\n```", content, re.DOTALL):
        doc_indicators += 1

    # 检查图片或链接
    if re.search(r"!\[.*?\]\(.*?\)|(?<!!)\[.*?\]\(.*?\)", content):
        doc_indicators += 1

    # 如果有至少两个文档指标，认为是文档
    return doc_indicators >= 2
