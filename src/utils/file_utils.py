#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具

提供常用的文件操作功能
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def ensure_directory_exists(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建它

    Args:
        directory_path: 目录路径

    Returns:
        bool: 如果目录存在或创建成功则返回True，否则返回False
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory_path}: {str(e)}")
        return False


def file_exists(file_path: str) -> bool:
    """
    检查文件是否存在

    Args:
        file_path: 文件路径

    Returns:
        bool: 如果文件存在则为True，否则为False
    """
    return os.path.isfile(file_path)


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    读取JSON文件并返回解析后的数据

    Args:
        file_path: JSON文件路径

    Returns:
        Dict[str, Any]: 解析后的JSON数据

    Raises:
        FileNotFoundError: 如果文件不存在
        json.JSONDecodeError: 如果文件不是有效的JSON
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    将数据写入JSON文件

    Args:
        file_path: 要写入的文件路径
        data: 要写入的数据
        indent: JSON缩进级别

    Returns:
        bool: 如果写入成功返回True，否则返回False
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"写入JSON文件失败 {file_path}: {str(e)}")
        return False


def read_text_file(file_path: str) -> str:
    """
    读取文本文件并返回内容

    Args:
        file_path: 文本文件路径

    Returns:
        str: 文件内容

    Raises:
        FileNotFoundError: 如果文件不存在
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(file_path: str, content: str) -> None:
    """
    将文本内容写入文件

    Args:
        file_path: 要写入的文件路径
        content: 要写入的文本内容
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
