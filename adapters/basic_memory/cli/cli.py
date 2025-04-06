#!/usr/bin/env python3
"""
Basic Memory CLI主入口
提供统一的命令行接口
"""

import argparse
import sys
from pathlib import Path

from adapters.basic_memory.cli.export_cmd import export_cmd
from adapters.basic_memory.cli.import_cmd import main as import_cmd
from adapters.basic_memory.cli.parse_cmd import parse_cmd


def main():
    """CLI主入口函数"""
    parser = argparse.ArgumentParser(description="Basic Memory命令行工具", prog="basic-memory")

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 解析命令
    parse_parser = subparsers.add_parser("parse", help="解析文档并提取实体关系")
    parse_parser.add_argument("target", help="要解析的文件或目录路径")
    parse_parser.add_argument("--parser", "-p", help="解析器类型 (默认: regex)", default="regex")
    parse_parser.add_argument("--output", "-o", help="解析结果输出目录")
    parse_parser.add_argument("--pattern", help="文件名匹配模式 (目录模式下)")
    parse_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录 (目录模式下)")

    # 导出命令
    export_parser = subparsers.add_parser("export", help="导出解析结果到其他格式")
    export_parser.add_argument("target", help="要导出的文件或目录路径")
    export_parser.add_argument("--format", "-f", help="导出格式 (默认: obsidian)", default="obsidian")
    export_parser.add_argument("--output", "-o", help="导出结果输出目录")
    export_parser.add_argument("--pattern", help="文件名匹配模式 (目录模式下)")
    export_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索子目录 (目录模式下)")

    # 导入命令
    import_parser = subparsers.add_parser("import", help="批量导入文档到数据库")
    import_parser.add_argument("source_dir", help="源文档目录")
    import_parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="Basic Memory数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )
    import_parser.add_argument(
        "--parser",
        choices=["openai", "ollama"],
        default="ollama",
        help="解析器类型 (默认: ollama)",
    )
    import_parser.add_argument(
        "--model",
        default="mistral",
        help="模型名称 (默认: mistral)",
    )

    # 版本命令
    version_parser = subparsers.add_parser("version", help="显示版本信息")

    # 解析参数
    args = parser.parse_args()

    # 执行命令
    if args.command == "parse":
        # 传递参数并调用parse_cmd内部功能
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        parse_cmd()
    elif args.command == "export":
        # 传递参数并调用export_cmd内部功能
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        export_cmd()
    elif args.command == "import":
        # 传递参数并调用import_cmd内部功能
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        import_cmd()
    elif args.command == "version":
        print("Basic Memory CLI 版本 0.1.0")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
