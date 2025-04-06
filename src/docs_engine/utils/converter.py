#!/usr/bin/env python
"""
标准Markdown和Obsidian格式之间的转换工具。

本模块提供两个主要的转换类：
- MDToObsidian：将标准Markdown转换为Obsidian Wiki风格
- ObsidianToMD：将Obsidian Wiki风格转换为标准Markdown

这个适配层利用了现有的开源库，避免重复造轮子。
"""

import logging

from adapters.obsidian.converter.constants import DEFAULT_EXCLUDE_PATTERNS
from adapters.obsidian.converter.md_to_obsidian import MDToObsidian
from adapters.obsidian.converter.obsidian_to_md import ObsidianToMD

# 为了保持向后兼容性，导出所有类和常量
__all__ = ["MDToObsidian", "ObsidianToMD", "DEFAULT_EXCLUDE_PATTERNS"]


def convert_markdown(content, format_type="obsidian", **kwargs):
    """
    转换Markdown内容。

    Args:
        content: 要转换的内容
        format_type: 转换目标格式，支持"obsidian"或"markdown"
        **kwargs: 传递给具体转换器的参数

    Returns:
        str: 转换后的内容
    """
    if format_type == "obsidian":
        converter = MDToObsidian(**kwargs)
        return converter.convert_content(content, "", "")
    else:
        converter = ObsidianToMD(**kwargs)
        return converter.convert_content(content, "", "")


def convert_wikilinks(content, to_standard=True, **kwargs):
    """
    转换Wiki链接。

    Args:
        content: 要转换的内容
        to_standard: 如果为True，将Wiki链接转换为标准链接；否则反之
        **kwargs: 传递给具体转换器的参数

    Returns:
        str: 转换后的内容
    """
    if to_standard:
        converter = ObsidianToMD(**kwargs)
        return converter.convert_content(content, "", "")
    else:
        converter = MDToObsidian(**kwargs)
        return converter.convert_content(content, "", "")
