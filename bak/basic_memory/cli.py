#!/usr/bin/env python3
"""
Basic Memory 命令行接口
提供统一的命令行入口和解析逻辑
"""

import argparse
import sys

from adapters.basic_memory.cli.export_cmd import handle_export, setup_export_parser
from adapters.basic_memory.cli.import_cmd import handle_import, setup_import_parser
from adapters.basic_memory.cli.parse_cmd import handle_parse, setup_parse_parser
from adapters.basic_memory.cli.query_cmd import handle_query, setup_query_parser


def main():
    """主函数，处理命令行参数并调用相应的处理函数"""
    # 创建顶级解析器
    parser = argparse.ArgumentParser(
        description="Basic Memory 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 设置各子命令解析器
    parse_parser = setup_parse_parser(subparsers)
    export_parser = setup_export_parser(subparsers)
    import_parser = setup_import_parser(subparsers)
    query_parser = setup_query_parser(subparsers)

    # 解析命令行参数
    args = parser.parse_args()

    # 如果没有提供子命令，则显示帮助信息
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 根据子命令调用相应的处理函数
    if args.command == "parse":
        handle_parse(args)
    elif args.command == "export":
        handle_export(args)
    elif args.command == "import":
        handle_import(args)
    elif args.command == "query":
        handle_query(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
