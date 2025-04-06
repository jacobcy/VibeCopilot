#!/usr/bin/env python
"""
标准Markdown和Obsidian格式之间的转换工具。

本模块提供两个主要的转换类：
- MDToObsidian：将标准Markdown转换为Obsidian Wiki风格
- ObsidianToMD：将Obsidian Wiki风格转换为标准Markdown

这个适配层利用了现有的开源库，避免重复造轮子。
"""

import logging
import warnings

from scripts.docs.utils.converter import DEFAULT_EXCLUDE_PATTERNS, MDToObsidian, ObsidianToMD

# 废弃警告
warnings.warn(
    "converter.py已重构为模块化结构，请直接从scripts.docs.utils.converter导入所需类",
    DeprecationWarning,
    stacklevel=2,
)

# 为了保持向后兼容性，导出所有类和常量
__all__ = ["MDToObsidian", "ObsidianToMD", "DEFAULT_EXCLUDE_PATTERNS"]
