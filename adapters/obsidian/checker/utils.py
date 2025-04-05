#!/usr/bin/env python
"""
Obsidian语法检查工具的工具函数
"""

from pathlib import Path
from typing import List, Optional, Tuple


def resolve_link_path(
    link_target: str, current_dir: Path, extensions: List[str] = None
) -> Optional[Path]:
    """解析Obsidian链接目标的实际文件路径

    Args:
        link_target: 链接目标名称
        current_dir: 当前文件所在目录
        extensions: 可能的文件扩展名列表，默认为['.md', '.pdf', '.png', '.jpg', '.jpeg']

    Returns:
        解析后的路径，如果找不到则返回None
    """
    if extensions is None:
        extensions = [".md", ".pdf", ".png", ".jpg", ".jpeg"]

    # 检查是否是相对路径
    if "/" in link_target:
        # 按路径解析
        parts = link_target.split("/")
        target_dir = current_dir
        for i, part in enumerate(parts[:-1]):
            if part == "..":
                target_dir = target_dir.parent
            elif part and part != ".":
                target_dir = target_dir / part

        basename = parts[-1]
    else:
        # 不包含路径分隔符，直接在当前目录查找
        target_dir = current_dir
        basename = link_target

    # 尝试每个可能的扩展名
    for ext in extensions:
        target_path = target_dir / f"{basename}{ext}"
        if target_path.exists():
            return target_path

    # 如果没有指定扩展名，可能是文件名已经包含扩展名
    direct_path = target_dir / basename
    if direct_path.exists():
        return direct_path

    # 最后尝试在所有子目录中搜索
    for subdir in current_dir.glob("**/"):
        for ext in extensions:
            target_path = subdir / f"{basename}{ext}"
            if target_path.exists():
                return target_path

        direct_path = subdir / basename
        if direct_path.exists():
            return direct_path

    return None


def create_line_map(content: str) -> List[int]:
    """创建字符位置到行号的映射

    Args:
        content: 文档内容

    Returns:
        每行起始字符位置的列表
    """
    line_starts = [0]
    for i, char in enumerate(content):
        if char == "\n":
            line_starts.append(i + 1)
    return line_starts


def get_line_col(pos: int, line_map: List[int]) -> Tuple[int, int]:
    """获取字符位置对应的行和列

    Args:
        pos: 字符位置
        line_map: 行映射列表

    Returns:
        (行号，列号) 从1开始计数
    """
    # 二分查找找到对应的行
    left, right = 0, len(line_map) - 1
    line = 0

    while left <= right:
        mid = (left + right) // 2
        if line_map[mid] <= pos:
            line = mid
            left = mid + 1
        else:
            right = mid - 1

    # 计算列号 (pos - 行起始位置 + 1)
    column = pos - line_map[line] + 1

    # 行号从1开始
    return line + 1, column
