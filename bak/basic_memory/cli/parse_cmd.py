#!/usr/bin/env python3
"""
单文档解析命令行工具
提供解析Markdown文档，提取实体和关系的命令行接口
使用content_parser进行主要解析工作
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from adapters.basic_memory.config import DEFAULT_OUTPUT_PATH, DEFAULT_PARSER_CONFIG, PARSER_TYPE_MAPPING
from adapters.basic_memory.db.memory_store import MemoryStore
from adapters.basic_memory.parsers.regex_parser import parse_with_regex
from adapters.basic_memory.utils.file_utils import ensure_directory, find_files, get_file_type
from adapters.basic_memory.utils.formatters import convert_to_entity_format, print_entity_visualization
from adapters.content_parser.utils.parser import parse_file as content_parse_file


def create_parser_instance(parser_type: str, config: Optional[Dict[str, Any]] = None):
    """创建解析器实例

    Args:
        parser_type: 解析器类型
        config: 解析器配置

    Returns:
        解析器实例
    """
    if parser_type not in PARSER_TYPE_MAPPING:
        raise ValueError(f"不支持的解析器类型: {parser_type}")

    class_name = PARSER_TYPE_MAPPING[parser_type]
    module_name = f"adapters.basic_memory.parsers.{parser_type}_parser"

    try:
        module = importlib.import_module(module_name)
        parser_class = getattr(module, class_name)
        return parser_class(config)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"无法导入解析器 {class_name}: {e}")


def parse_file(
    file_path: Union[str, Path],
    parser_type: str = "regex",
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """解析单个文件

    Args:
        file_path: 文件路径
        parser_type: 解析器类型
        output_dir: 输出目录
        config: 解析器配置

    Returns:
        Dict: 解析结果
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"文件不存在或不是文件: {path}")

    # 创建解析器实例
    parser = create_parser_instance(parser_type, config)

    # 解析文件
    print(f"正在解析文件: {path}")
    result = parser.parse_file(path)

    # 保存结果
    if output_dir:
        out_dir = ensure_directory(output_dir)
        output_file = out_dir / f"{path.stem}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"解析结果已保存到: {output_file}")

    return result


def parse_directory(
    directory: Union[str, Path],
    parser_type: str = "regex",
    output_dir: Optional[Union[str, Path]] = None,
    pattern: str = "*.*",
    recursive: bool = True,
    file_types: Optional[List[str]] = None,
    max_files: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """解析目录中的文件

    Args:
        directory: 目录路径
        parser_type: 解析器类型
        output_dir: 输出目录
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录
        file_types: 要过滤的文件类型列表
        max_files: 最大处理文件数
        config: 解析器配置

    Returns:
        List[Dict]: 解析结果列表
    """
    dir_path = Path(directory) if isinstance(directory, str) else directory

    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"目录不存在: {dir_path}")

    # 查找文件
    files = find_files(dir_path, pattern, recursive, file_types)

    if max_files:
        files = files[:max_files]

    if not files:
        print(f"在目录 {dir_path} 中没有找到匹配的文件")
        return []

    # 创建输出目录
    if output_dir:
        out_dir = ensure_directory(output_dir)
    else:
        out_dir = None

    # 创建解析器实例
    parser = create_parser_instance(parser_type, config)

    # 解析文件
    results = []
    for i, file in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] 正在解析: {file}")
            result = parser.parse_file(file)
            results.append(result)

            # 保存结果
            if out_dir:
                output_file = out_dir / f"{file.stem}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"解析文件 {file} 时出错: {e}")

    return results


def setup_parse_parser(subparsers):
    """设置解析命令的解析器

    Args:
        subparsers: 父解析器的子解析器

    Returns:
        argparse.ArgumentParser: 解析命令解析器
    """
    parse_parser = subparsers.add_parser("parse", help="解析文档并生成结构化数据")

    # 添加子命令
    parse_subparsers = parse_parser.add_subparsers(dest="parse_type", help="解析类型")

    # 设置正则表达式解析
    regex_parser = parse_subparsers.add_parser("regex", help="使用正则表达式解析文档")

    regex_parser.add_argument("target", help="要解析的文件或目录路径")

    regex_parser.add_argument("--output", "-o", help="输出目录路径")

    regex_parser.add_argument("--pattern", default="*.md", help="文件名匹配模式（目录模式下有效）")

    regex_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录（目录模式下有效）")

    regex_parser.add_argument("--encoding", default="utf-8", help="文件编码")

    # 添加更多解析器...

    return parse_parser


def handle_parse(args):
    """处理解析命令

    Args:
        args: 解析后的命令行参数
    """
    if args.parse_type == "regex":
        _handle_regex_parse(args)
    else:
        print(f"错误: 未知的解析类型: {args.parse_type}")
        sys.exit(1)


def _handle_regex_parse(args):
    """处理正则表达式解析

    Args:
        args: 解析后的命令行参数
    """
    target_path = Path(args.target)

    # 设置输出目录
    if args.output:
        output_dir = ensure_directory(args.output)
    else:
        # 默认输出到target同级的output目录
        if target_path.is_file():
            output_dir = ensure_directory(target_path.parent / "output")
        else:
            output_dir = ensure_directory(target_path / "output")

    try:
        if target_path.is_file():
            # 解析单个文件
            _parse_file_with_regex(target_path, output_dir, encoding=args.encoding)
        elif target_path.is_dir():
            # 解析目录
            _parse_directory_with_regex(
                target_path,
                output_dir,
                pattern=args.pattern,
                recursive=not args.no_recursive,
                encoding=args.encoding,
            )
        else:
            print(f"目标路径不存在: {target_path}")
            sys.exit(1)
    except Exception as e:
        print(f"解析过程中出错: {e}")
        sys.exit(1)


def _parse_file_with_regex(file_path: Union[str, Path], output_dir: Union[str, Path], encoding: str = "utf-8") -> None:
    """使用正则表达式解析单个文件

    Args:
        file_path: 文件路径
        output_dir: 输出目录路径
        encoding: 文件编码
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"文件不存在或不是文件: {path}")

    # 读取文件内容
    try:
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"无法使用 {encoding} 编码读取文件 {path}，尝试使用 utf-8")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

    # 解析文件
    print(f"正在解析文件: {path}")
    result = parse_with_regex(content, str(path))

    # 保存结果
    out_path = Path(output_dir) / f"{path.stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"解析完成，结果保存在: {out_path}")


def _parse_directory_with_regex(
    directory: Union[str, Path],
    output_dir: Union[str, Path],
    pattern: str = "*.md",
    recursive: bool = True,
    encoding: str = "utf-8",
) -> None:
    """使用正则表达式解析目录中的文件

    Args:
        directory: 目录路径
        output_dir: 输出目录路径
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录
        encoding: 文件编码
    """
    dir_path = Path(directory) if isinstance(directory, str) else directory

    if not dir_path.exists() or not dir_path.is_dir():
        raise ValueError(f"目录不存在: {dir_path}")

    # 查找文件
    files = find_files(dir_path, pattern, recursive)

    if not files:
        print(f"在目录 {dir_path} 中没有找到匹配的文件")
        return

    # 解析文件
    for i, file in enumerate(files, 1):
        try:
            print(f"[{i}/{len(files)}] 正在解析: {file}")
            _parse_file_with_regex(file, output_dir, encoding)
        except Exception as e:
            print(f"解析文件 {file} 时出错: {e}")

    print(f"所有文件解析完成，结果保存在: {output_dir}")


def parse_cmd():
    """解析命令行入口"""
    parser = argparse.ArgumentParser(description="解析文档并生成结构化数据")

    # 添加子命令
    subparsers = parser.add_subparsers(dest="parse_type", help="解析类型")

    # 设置正则表达式解析
    regex_parser = subparsers.add_parser("regex", help="使用正则表达式解析文档")

    regex_parser.add_argument("target", help="要解析的文件或目录路径")

    regex_parser.add_argument("--output", "-o", help="输出目录路径")

    regex_parser.add_argument("--pattern", default="*.md", help="文件名匹配模式（目录模式下有效）")

    regex_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录（目录模式下有效）")

    regex_parser.add_argument("--encoding", default="utf-8", help="文件编码")

    # 解析参数
    args = parser.parse_args()

    # 处理命令
    if not args.parse_type:
        parser.print_help()
        sys.exit(1)

    handle_parse(args)


if __name__ == "__main__":
    parse_cmd()
