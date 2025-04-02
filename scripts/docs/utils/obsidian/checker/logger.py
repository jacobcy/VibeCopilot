#!/usr/bin/env python
"""
Obsidian语法检查工具的日志模块
"""

import logging


def setup_logging(verbose: bool = False) -> logging.Logger:
    """设置日志记录器

    Args:
        verbose: 是否输出详细日志

    Returns:
        日志记录器
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return logging.getLogger("obsidian_syntax_checker")
