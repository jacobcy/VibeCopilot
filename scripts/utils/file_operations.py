#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件和目录操作工具.

提供处理文件和目录的通用函数，如读写文件、创建目录结构等。
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union


def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建.

    Args:
        directory_path: 目录路径

    Returns:
        Path: 目录路径的Path对象
    """
    path = Path(directory_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise NotADirectoryError(f"{directory_path}不是一个目录")
    return path


def read_file(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    读取文件内容.

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认为utf-8

    Returns:
        str: 文件内容

    Raises:
        FileNotFoundError: 如果文件不存在
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """
    写入内容到文件.

    如果文件所在目录不存在，会自动创建。

    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认为utf-8
    """
    path = Path(file_path)
    ensure_directory(path.parent)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def read_json(file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
    """
    读取JSON文件并返回字典.

    Args:
        file_path: JSON文件路径
        encoding: 文件编码，默认为utf-8

    Returns:
        Dict[str, Any]: 解析后的JSON数据

    Raises:
        FileNotFoundError: 如果文件不存在
        json.JSONDecodeError: 如果JSON解析失败
    """
    content = read_file(file_path, encoding)
    return json.loads(content)  # type: ignore[no-any-return]


def write_json(
    file_path: Union[str, Path], data: Dict[str, Any], encoding: str = "utf-8", indent: int = 2
) -> None:
    """
    将字典写入JSON文件.

    Args:
        file_path: JSON文件路径
        data: 要写入的数据
        encoding: 文件编码，默认为utf-8
        indent: JSON缩进值，默认为2
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=indent)
    write_file(file_path, json_str, encoding)


def list_files(
    directory_path: Union[str, Path], pattern: Optional[str] = None, recursive: bool = False
) -> List[Path]:
    """
    列出目录中的文件.

    Args:
        directory_path: 目录路径
        pattern: 文件模式(glob pattern)，如"*.py"
        recursive: 是否递归搜索子目录

    Returns:
        List[Path]: 文件路径列表
    """
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return []

    if recursive:
        if pattern:
            return list(path.glob(f"**/{pattern}"))
        else:
            return [p for p in path.glob("**/*") if p.is_file()]
    else:
        if pattern:
            return list(path.glob(pattern))
        else:
            return [p for p in path.iterdir() if p.is_file()]


def copy_directory_structure(
    source_dir: Union[str, Path],
    target_dir: Union[str, Path],
    ignore_patterns: Optional[Set[str]] = None,
) -> None:
    """
    复制目录结构，包括所有子目录和文件.

    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        ignore_patterns: 要忽略的文件/目录模式集合
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    if not source_path.exists() or not source_path.is_dir():
        raise NotADirectoryError(f"源目录不存在: {source_dir}")

    # 创建目标目录
    ensure_directory(target_path)

    def ignore_func(dir_path: str, names: List[str]) -> List[str]:
        if ignore_patterns is None:
            return []

        # 转换为相对路径
        rel_path = os.path.relpath(dir_path, source_path)
        if rel_path == ".":
            rel_path = ""

        ignore_list = []
        for name in names:
            # 构建相对路径
            if rel_path:
                item_rel_path = f"{rel_path}/{name}"
            else:
                item_rel_path = name

            # 检查是否匹配忽略模式
            for pattern in ignore_patterns:
                if Path(item_rel_path).match(pattern):
                    ignore_list.append(name)
                    break

        return ignore_list

    # 复制目录结构
    shutil.copytree(source_path, target_path, ignore=ignore_func, dirs_exist_ok=True)


def create_directory_structure(structure: Dict[str, Any], base_dir: Union[str, Path]) -> None:
    """
    根据字典定义创建目录结构.

    结构字典格式:
    {
        "dir1": {              # 目录名
            "file1.txt": "内容",  # 文件名: 内容
            "subdir": {         # 子目录
                "file2.txt": "内容"
            }
        },
        "dir2": None           # 空目录
    }

    Args:
        structure: 目录结构字典
        base_dir: 基础目录路径
    """
    base_path = Path(base_dir)
    ensure_directory(base_path)

    def _create_structure(struct: Dict[str, Any], current_path: Path) -> None:
        for name, content in struct.items():
            path = current_path / name

            if content is None:
                # 创建空目录
                ensure_directory(path)
            elif isinstance(content, dict):
                # 创建目录及其内容
                ensure_directory(path)
                _create_structure(content, path)
            else:
                # 创建文件
                write_file(path, str(content))

    _create_structure(structure, base_path)


if __name__ == "__main__":
    # 简单的使用示例
    example_structure = {
        "example_dir": {
            "file1.txt": "Hello, World!",
            "subdir": {"file2.txt": "This is a test file."},
        },
        "empty_dir": None,
    }

    # 创建示例结构
    create_directory_structure(example_structure, "./example_output")
    print("示例目录结构已创建在 ./example_output")
