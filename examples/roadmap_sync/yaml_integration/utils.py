#!/usr/bin/env python
"""
YAML集成工具函数

提供文件读写等通用工具函数
"""

import logging
from typing import Optional

# 配置日志
logger = logging.getLogger("yaml_integration.utils")


def read_file_content(file_path: str) -> Optional[str]:
    """
    读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        Optional[str]: 文件内容，失败则返回None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
        return None


def write_file_content(file_path: str, content: str) -> bool:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容

    Returns:
        bool: 是否成功写入
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")
        return False
