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

# Import config getter
from src.core.config import ConfigError, get_config

logger = logging.getLogger(__name__)


def get_data_path(*subdirs: str, filename: Optional[str] = None) -> str:
    """获取数据目录下指定子目录和文件的绝对路径。

    Args:
        *subdirs: 任意数量的子目录名。
        filename: 可选的文件名。

    Returns:
        str: 构造的绝对路径。

    Raises:
        ConfigError: 如果无法获取'paths.data_dir'配置。
        OSError: 如果创建目录失败。
    """
    try:
        config = get_config()
        # 获取已解析为绝对路径的data_dir
        data_dir = config.get("paths.data_dir")
        if not data_dir:
            raise ConfigError("无法从配置中获取 'paths.data_dir'")

        # 构造路径
        path_parts = [data_dir] + list(subdirs)
        if filename:
            target_path = os.path.join(*path_parts, filename)
            # 确保父目录存在
            target_dir = os.path.dirname(target_path)
        else:
            # 如果没有文件名，则目标是目录本身
            target_path = os.path.join(*path_parts)
            target_dir = target_path

        # 创建目录（如果不存在）
        os.makedirs(target_dir, exist_ok=True)
        logger.debug(f"确保数据路径存在: {target_dir}")

        return target_path

    except ConfigError as ce:
        logger.error(f"配置错误: {ce}")
        raise
    except OSError as oe:
        logger.error(f"创建数据目录或文件路径失败: {oe}")
        raise
    except Exception as e:
        logger.error(f"获取数据路径时发生意外错误: {e}", exc_info=True)
        raise ConfigError(f"获取数据路径时发生意外错误: {e}")


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


def get_relative_path(path: str, base_path: Optional[str] = None) -> str:
    """
    获取相对于基准路径的相对路径

    Args:
        path: 要转换的路径
        base_path: 基准路径，如果不提供则使用当前工作目录

    Returns:
        str: 相对路径
    """
    if base_path is None:
        base_path = os.getcwd()

    try:
        return os.path.relpath(path, base_path)
    except ValueError:
        # 如果路径在不同的驱动器上，返回原始路径
        return path
