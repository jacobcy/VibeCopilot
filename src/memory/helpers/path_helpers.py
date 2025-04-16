#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径处理工具

提供处理文件路径和目录的工具函数，包括路径验证、规范化和转换等功能。
"""

import os
import pathlib
import re
from typing import List, Optional, Tuple, Union
from urllib.parse import quote, unquote, urlparse

# 常量定义
VALID_FILENAME_PATTERN = re.compile(r'^[^\\/:"*?<>|]+$')  # Windows和类Unix系统通用的有效文件名模式
INVALID_PATH_CHARS = set('<>:"|?*\\/')  # 无效的路径字符


def normalize_path(path: str) -> str:
    """
    规范化路径，处理路径分隔符和相对路径。

    Args:
        path: 原始路径

    Returns:
        规范化后的路径
    """
    if not path:
        return ""

    # 规范化路径分隔符为系统标准
    path = os.path.normpath(path)

    # 确保路径使用标准分隔符
    return pathlib.Path(path).as_posix()


def join_paths(*paths: str) -> str:
    """
    连接多个路径片段。

    Args:
        *paths: 要连接的路径片段

    Returns:
        连接后的路径
    """
    if not paths:
        return ""

    # 过滤空路径
    valid_paths = [p for p in paths if p]

    if not valid_paths:
        return ""

    # 连接路径
    joined = os.path.join(*valid_paths)

    # 规范化
    return normalize_path(joined)


def get_parent_dir(path: str) -> str:
    """
    获取路径的父目录。

    Args:
        path: 文件或目录路径

    Returns:
        父目录路径
    """
    if not path:
        return ""

    return os.path.dirname(normalize_path(path))


def get_filename(path: str, with_extension: bool = True) -> str:
    """
    从路径中提取文件名。

    Args:
        path: 文件路径
        with_extension: 是否包含扩展名

    Returns:
        文件名
    """
    if not path:
        return ""

    filename = os.path.basename(normalize_path(path))

    if not with_extension:
        filename = os.path.splitext(filename)[0]

    return filename


def get_extension(path: str) -> str:
    """
    从文件路径中提取扩展名。

    Args:
        path: 文件路径

    Returns:
        文件扩展名（包含点号）
    """
    if not path:
        return ""

    _, ext = os.path.splitext(path)
    return ext.lower()


def is_valid_filename(filename: str) -> bool:
    """
    检查文件名是否有效（不含非法字符）。

    Args:
        filename: 要检查的文件名

    Returns:
        如果文件名有效则返回True，否则返回False
    """
    if not filename:
        return False

    return bool(VALID_FILENAME_PATTERN.match(filename))


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    清理文件名，替换或移除无效字符。

    Args:
        filename: 原始文件名
        replacement: 用于替换无效字符的字符

    Returns:
        清理后的文件名
    """
    if not filename:
        return ""

    # 替换无效字符
    cleaned = ""
    for char in filename:
        if char in INVALID_PATH_CHARS:
            cleaned += replacement
        else:
            cleaned += char

    # 处理首尾空格
    cleaned = cleaned.strip()

    # 确保不是空字符串
    if not cleaned:
        cleaned = "unnamed"

    return cleaned


def ensure_dir_exists(directory: str, create: bool = True) -> bool:
    """
    确保目录存在，如果不存在可以选择创建。

    Args:
        directory: 目录路径
        create: 如果目录不存在是否创建

    Returns:
        如果目录存在或创建成功则返回True，否则返回False
    """
    if not directory:
        return False

    # 规范化路径
    directory = normalize_path(directory)

    # 检查目录是否存在
    if os.path.exists(directory) and os.path.isdir(directory):
        return True

    # 如果目录不存在且需要创建
    if create:
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except OSError:
            return False

    return False


def is_subpath(parent: str, child: str) -> bool:
    """
    检查一个路径是否是另一个路径的子路径。

    Args:
        parent: 父路径
        child: 子路径

    Returns:
        如果child是parent的子路径则返回True，否则返回False
    """
    if not parent or not child:
        return False

    # 规范化路径
    parent = normalize_path(parent)
    child = normalize_path(child)

    # 使用pathlib进行比较
    return str(pathlib.Path(child)).startswith(str(pathlib.Path(parent)))


def make_relative_path(base_path: str, full_path: str) -> str:
    """
    将绝对路径转换为相对于基础路径的相对路径。

    Args:
        base_path: 基础路径
        full_path: 完整路径

    Returns:
        相对路径
    """
    if not base_path or not full_path:
        return full_path

    # 规范化路径
    base_path = normalize_path(base_path)
    full_path = normalize_path(full_path)

    # 使用pathlib生成相对路径
    try:
        return str(pathlib.Path(full_path).relative_to(pathlib.Path(base_path)))
    except ValueError:
        # 如果不是子路径，返回原始路径
        return full_path


def expand_user_path(path: str) -> str:
    """
    展开用户路径（如 ~/Documents）。

    Args:
        path: 包含用户路径的字符串

    Returns:
        展开后的路径
    """
    if not path:
        return ""

    return os.path.expanduser(path)


def find_common_prefix(paths: List[str]) -> str:
    """
    找出一组路径的共同前缀。

    Args:
        paths: 路径列表

    Returns:
        共同前缀路径
    """
    if not paths:
        return ""

    # 过滤空路径
    valid_paths = [normalize_path(p) for p in paths if p]

    if not valid_paths:
        return ""

    # 使用os.path.commonpath找出共同前缀
    try:
        return os.path.commonpath(valid_paths)
    except ValueError:
        return ""


def path_to_permalink(path: str) -> str:
    """
    将文件路径转换为永久链接格式。

    Args:
        path: 文件路径

    Returns:
        永久链接
    """
    if not path:
        return ""

    # 规范化路径
    path = normalize_path(path)

    # 移除可能的文件前缀（如file://）
    if path.startswith("file://"):
        path = path[7:]

    # 编码路径中的特殊字符
    path_parts = path.split("/")
    encoded_parts = [quote(part, safe="") for part in path_parts]

    # 构建permalink
    return "memory://" + "/".join(encoded_parts)


def permalink_to_path(permalink: str) -> str:
    """
    将永久链接转换回文件路径。

    Args:
        permalink: 永久链接

    Returns:
        文件路径
    """
    if not permalink or not permalink.startswith("memory://"):
        return permalink

    # 移除前缀
    path = permalink[9:]

    # 解码特殊字符
    path_parts = path.split("/")
    decoded_parts = [unquote(part) for part in path_parts]

    # 构建路径
    return normalize_path("/".join(decoded_parts))


def is_url(path: str) -> bool:
    """
    检查路径是否为URL。

    Args:
        path: 要检查的路径

    Returns:
        如果是URL则返回True，否则返回False
    """
    if not path:
        return False

    # 检查常见协议前缀
    parsed = urlparse(path)
    return bool(parsed.scheme and parsed.netloc)


def is_permalink(path: str) -> bool:
    """
    检查路径是否为永久链接。

    Args:
        path: 要检查的路径

    Returns:
        如果是永久链接则返回True，否则返回False
    """
    if not path:
        return False

    return path.startswith("memory://")


def get_path_type(path: str) -> str:
    """
    获取路径类型。

    Args:
        path: 要检查的路径

    Returns:
        路径类型："file"、"directory"、"url"、"permalink"或"unknown"
    """
    if not path:
        return "unknown"

    if is_url(path):
        return "url"

    if is_permalink(path):
        return "permalink"

    # 规范化路径
    norm_path = normalize_path(path)

    if os.path.exists(norm_path):
        if os.path.isdir(norm_path):
            return "directory"
        elif os.path.isfile(norm_path):
            return "file"

    return "unknown"


def resolve_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    解析路径，将相对路径转换为绝对路径。

    Args:
        path: 要解析的路径
        base_dir: 基础目录，用于解析相对路径

    Returns:
        解析后的绝对路径
    """
    if not path:
        return ""

    # 处理URL和永久链接
    if is_url(path) or is_permalink(path):
        return path

    # 展开用户路径
    path = expand_user_path(path)

    # 如果是绝对路径
    if os.path.isabs(path):
        return normalize_path(path)

    # 如果是相对路径且提供了基础目录
    if base_dir:
        base_dir = expand_user_path(base_dir)
        return normalize_path(os.path.join(base_dir, path))

    # 如果是相对路径但没有提供基础目录，使用当前工作目录
    return normalize_path(os.path.abspath(path))


def list_files(directory: str, pattern: Optional[str] = None, recursive: bool = False, include_hidden: bool = False) -> List[str]:
    """
    列出目录中的文件。

    Args:
        directory: 目录路径
        pattern: 文件名匹配模式（glob格式）
        recursive: 是否递归搜索子目录
        include_hidden: 是否包含隐藏文件

    Returns:
        文件路径列表
    """
    if not directory or not os.path.isdir(directory):
        return []

    # 规范化目录路径
    directory = normalize_path(directory)

    # 获取所有文件
    if recursive:
        walker = os.walk(directory)
        files = []

        for root, _, filenames in walker:
            for filename in filenames:
                # 跳过隐藏文件
                if not include_hidden and filename.startswith("."):
                    continue

                file_path = os.path.join(root, filename)
                files.append(normalize_path(file_path))
    else:
        files = []

        for entry in os.listdir(directory):
            # 跳过隐藏文件
            if not include_hidden and entry.startswith("."):
                continue

            file_path = os.path.join(directory, entry)
            if os.path.isfile(file_path):
                files.append(normalize_path(file_path))

    # 如果有匹配模式，进行过滤
    if pattern:
        import fnmatch

        files = [f for f in files if fnmatch.fnmatch(get_filename(f), pattern)]

    return files


def get_file_size(path: str) -> int:
    """
    获取文件大小（字节）。

    Args:
        path: 文件路径

    Returns:
        文件大小（字节），如果文件不存在返回-1
    """
    if not path or not os.path.isfile(path):
        return -1

    try:
        return os.path.getsize(path)
    except OSError:
        return -1


def format_file_size(size: int, decimal_places: int = 2) -> str:
    """
    格式化文件大小，使用合适的单位。

    Args:
        size: 文件大小（字节）
        decimal_places: 小数位数

    Returns:
        格式化后的文件大小字符串（如2.5 KB, 1.8 MB）
    """
    if size < 0:
        return "Unknown"

    # 定义单位
    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    # 选择合适的单位
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    # 格式化结果
    format_str = f"{{:.{decimal_places}f}} {{}}"
    return format_str.format(size, units[unit_index])


def get_file_info(path: str) -> dict:
    """
    获取文件的详细信息。

    Args:
        path: 文件路径

    Returns:
        包含文件信息的字典
    """
    if not path or not os.path.exists(path):
        return {"exists": False, "type": "unknown", "path": path}

    info = {
        "exists": True,
        "path": normalize_path(path),
        "name": get_filename(path),
        "basename": get_filename(path, with_extension=False),
        "extension": get_extension(path),
        "parent_dir": get_parent_dir(path),
        "is_absolute": os.path.isabs(path),
    }

    if os.path.isfile(path):
        info.update(
            {
                "type": "file",
                "size": get_file_size(path),
                "formatted_size": format_file_size(get_file_size(path)),
                "last_modified": os.path.getmtime(path),
            }
        )
    elif os.path.isdir(path):
        info.update({"type": "directory"})

    return info
