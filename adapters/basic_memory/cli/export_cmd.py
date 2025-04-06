#!/usr/bin/env python3
"""
导出命令行模块
提供将解析结果导出为不同格式的命令行接口
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from adapters.basic_memory.config import (
    DEFAULT_EXPORT_PATH,
    DEFAULT_OBSIDIAN_CONFIG,
    EXPORTER_TYPE_MAPPING,
)
from adapters.basic_memory.utils.file_utils import ensure_directory, find_files


def setup_export_parser(subparsers):
    """设置导出命令的解析器

    Args:
        subparsers: 父解析器的子解析器

    Returns:
        argparse.ArgumentParser: 导出命令解析器
    """
    export_parser = subparsers.add_parser("export", help="将解析结果导出为不同格式")

    export_parser.add_argument("target", help="要导出的文件或目录路径")

    export_parser.add_argument(
        "--format",
        "-f",
        choices=list(EXPORTER_TYPE_MAPPING.keys()),
        default="obsidian",
        help="导出格式",
    )

    export_parser.add_argument("--output", "-o", default=DEFAULT_EXPORT_PATH, help="导出结果输出目录")

    export_parser.add_argument("--pattern", default="*.json", help="文件名匹配模式（目录模式下有效）")

    export_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录（目录模式下有效）")

    export_parser.add_argument("--config", help="导出器配置文件路径（JSON格式）")

    return export_parser


def handle_export(args):
    """处理导出命令

    Args:
        args: 解析后的命令行参数
    """
    # 处理配置
    config = DEFAULT_OBSIDIAN_CONFIG.copy()
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                custom_config = json.load(f)
                config.update(custom_config)
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            sys.exit(1)

    # 导出目标
    target_path = Path(args.target)

    try:
        if target_path.is_file():
            # 导出单个文件
            export_file(
                target_path, exporter_type=args.format, output_dir=args.output, config=config
            )
        elif target_path.is_dir():
            # 导出目录
            export_directory(
                target_path,
                exporter_type=args.format,
                output_dir=args.output,
                pattern=args.pattern,
                recursive=not args.no_recursive,
                config=config,
            )
        else:
            print(f"目标路径不存在: {target_path}")
            sys.exit(1)
    except Exception as e:
        print(f"导出过程中出错: {e}")
        sys.exit(1)


def create_exporter_instance(exporter_type: str, config: Optional[Dict[str, Any]] = None):
    """创建导出器实例

    Args:
        exporter_type: 导出器类型
        config: 导出器配置

    Returns:
        导出器实例
    """
    if exporter_type not in EXPORTER_TYPE_MAPPING:
        raise ValueError(f"不支持的导出器类型: {exporter_type}")

    class_name = EXPORTER_TYPE_MAPPING[exporter_type]
    module_name = f"adapters.basic_memory.exporters.{exporter_type}_exporter"

    try:
        module = importlib.import_module(module_name)
        exporter_class = getattr(module, class_name)
        return exporter_class(config)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"无法导入导出器 {class_name}: {e}")


def export_file(
    file_path: Union[str, Path],
    exporter_type: str = "obsidian",
    output_dir: Union[str, Path] = DEFAULT_EXPORT_PATH,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """导出单个文件

    Args:
        file_path: 文件路径
        exporter_type: 导出器类型
        output_dir: 输出目录
        config: 导出器配置
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"文件不存在或不是文件: {path}")

    # 确保文件是JSON格式
    if path.suffix.lower() != ".json":
        raise ValueError(f"只支持导出JSON文件，当前文件: {path}")

    # 加载数据
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建导出器实例
    exporter = create_exporter_instance(exporter_type, config)

    # 确保输出目录存在
    out_dir = ensure_directory(output_dir)

    # 导出数据
    print(f"正在导出文件: {path}")
    # 确定输出文件名和路径
    if exporter_type == "obsidian":
        # Obsidian导出器会自己处理文件路径，我们只需要传递目录
        exporter.export(data, out_dir)
    else:
        # 其他导出器需要设置具体的输出文件
        output_file = out_dir / f"{path.stem}.{exporter_type}"
        exporter.export(data, output_file)

    print(f"导出完成，结果保存在: {out_dir}")


def export_directory(
    directory: Union[str, Path],
    exporter_type: str = "obsidian",
    output_dir: Union[str, Path] = DEFAULT_EXPORT_PATH,
    pattern: str = "*.json",
    recursive: bool = True,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """导出目录中的文件

    Args:
        directory: 目录路径
        exporter_type: 导出器类型
        output_dir: 输出目录
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录
        config: 导出器配置
    """
    dir_path = Path(directory) if isinstance(directory, str) else directory

    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"目录不存在: {dir_path}")

    # 查找JSON文件
    files = find_files(dir_path, pattern, recursive)

    if not files:
        print(f"在目录 {dir_path} 中没有找到匹配的JSON文件")
        return

    # 创建导出器实例
    exporter = create_exporter_instance(exporter_type, config)

    # 确保输出目录存在
    out_dir = ensure_directory(output_dir)

    # 导出文件
    for i, file in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] 正在导出: {file}")

            # 加载数据
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 导出数据
            if exporter_type == "obsidian":
                # Obsidian导出器会自己处理文件路径
                exporter.export(data, out_dir)
            else:
                # 其他导出器需要设置具体的输出文件
                output_file = out_dir / f"{file.stem}.{exporter_type}"
                exporter.export(data, output_file)

        except Exception as e:
            print(f"导出文件 {file} 时出错: {e}")

    print(f"所有文件导出完成，结果保存在: {out_dir}")


def export_cmd():
    """导出命令行入口"""
    parser = argparse.ArgumentParser(description="导出解析结果")

    parser.add_argument("target", help="要导出的文件或目录路径")

    parser.add_argument(
        "--format",
        "-f",
        choices=list(EXPORTER_TYPE_MAPPING.keys()),
        default="obsidian",
        help="导出格式",
    )

    parser.add_argument("--output", "-o", default=DEFAULT_EXPORT_PATH, help="导出结果输出目录")

    parser.add_argument("--pattern", default="*.json", help="文件名匹配模式（目录模式下有效）")

    parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录（目录模式下有效）")

    parser.add_argument("--config", help="导出器配置文件路径（JSON格式）")

    args = parser.parse_args()

    # 直接调用handle_export函数
    handle_export(args)


if __name__ == "__main__":
    export_cmd()
