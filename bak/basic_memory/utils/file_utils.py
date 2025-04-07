"""
文件操作工具函数
提供文件读写、批量处理等功能
"""

import glob
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from adapters.basic_memory.config import FILE_TYPE_MAPPING


def get_file_type(file_path: Union[str, Path]) -> str:
    """根据文件扩展名获取文件类型

    Args:
        file_path: 文件路径

    Returns:
        str: 文件类型
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path
    extension = path.suffix.lower()

    for file_type, extensions in FILE_TYPE_MAPPING.items():
        if extension in extensions:
            return file_type

    return "unknown"


def find_files(
    directory: Union[str, Path],
    pattern: str = "*.*",
    recursive: bool = True,
    file_types: Optional[List[str]] = None,
) -> List[Path]:
    """在指定目录中查找匹配的文件

    Args:
        directory: 目录路径
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录
        file_types: 要过滤的文件类型列表

    Returns:
        List[Path]: 匹配的文件路径列表
    """
    dir_path = Path(directory) if isinstance(directory, str) else directory

    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"目录不存在: {dir_path}")

    # 构建glob模式
    if recursive:
        glob_pattern = f"**/{pattern}"
    else:
        glob_pattern = pattern

    # 查找文件
    files = list(dir_path.glob(glob_pattern))

    # 过滤文件类型
    if file_types:
        filtered_files = []
        for file in files:
            if file.is_file():
                file_type = get_file_type(file)
                if file_type in file_types:
                    filtered_files.append(file)
        return filtered_files

    # 只返回文件，不返回目录
    return [f for f in files if f.is_file()]


def ensure_directory(directory: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径

    Returns:
        Path: 目录路径对象
    """
    dir_path = Path(directory) if isinstance(directory, str) else directory

    if not dir_path.exists():
        os.makedirs(dir_path, exist_ok=True)
    elif not dir_path.is_dir():
        raise NotADirectoryError(f"路径存在但不是目录: {dir_path}")

    return dir_path


def batch_process_files(
    directory: Union[str, Path],
    processor: Callable[[Path], Any],
    pattern: str = "*.*",
    recursive: bool = True,
    file_types: Optional[List[str]] = None,
    max_files: Optional[int] = None,
) -> List[Any]:
    """批量处理目录中的文件

    Args:
        directory: 目录路径
        processor: 文件处理函数，接收一个文件路径，返回处理结果
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录
        file_types: 要过滤的文件类型列表
        max_files: 最大处理文件数

    Returns:
        List[Any]: 处理结果列表
    """
    files = find_files(directory, pattern, recursive, file_types)

    if max_files:
        files = files[:max_files]

    results = []
    for file in files:
        try:
            result = processor(file)
            results.append(result)
        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")

    return results


def copy_files_to_directory(files: List[Union[str, Path]], target_directory: Union[str, Path], create_subdirs: bool = False) -> List[Path]:
    """将文件复制到目标目录

    Args:
        files: 要复制的文件路径列表
        target_directory: 目标目录
        create_subdirs: 是否在目标目录中创建子目录结构

    Returns:
        List[Path]: 复制后的文件路径列表
    """
    target_dir = ensure_directory(target_directory)
    copied_files = []

    for file in files:
        src_path = Path(file) if isinstance(file, str) else file

        if not src_path.exists() or not src_path.is_file():
            print(f"文件不存在或不是文件: {src_path}")
            continue

        if create_subdirs:
            # 保留子目录结构
            rel_path = src_path.relative_to(src_path.anchor)
            dst_path = target_dir / rel_path
            ensure_directory(dst_path.parent)
        else:
            # 直接复制到目标目录
            dst_path = target_dir / src_path.name

        try:
            shutil.copy2(src_path, dst_path)
            copied_files.append(dst_path)
        except Exception as e:
            print(f"复制文件 {src_path} 到 {dst_path} 时出错: {e}")

    return copied_files
