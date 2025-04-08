"""
模板命令模块

提供模板管理和生成的命令行功能
"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console

from .commands import register_template_commands
from .handlers import (
    handle_template_create,
    handle_template_delete,
    handle_template_export,
    handle_template_generate,
    handle_template_import,
    handle_template_list,
    handle_template_load,
    handle_template_show,
    handle_template_update,
)

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
console = Console()


def execute_template_command(args: argparse.Namespace) -> None:
    """
    执行模板命令

    Args:
        args: 命令行参数
    """
    # 创建命令处理映射
    handlers = {
        "list": handle_template_list,
        "show": handle_template_show,
        "import": handle_template_import,
        "create": handle_template_create,
        "update": handle_template_update,
        "delete": handle_template_delete,
        "generate": handle_template_generate,
        "load": handle_template_load,
        "export": handle_template_export,
    }

    # 获取子命令名称
    subcommand = getattr(args, "subcommand", None)

    # 执行对应的处理函数
    handler = handlers.get(subcommand)
    if handler:
        try:
            logger.debug(f"执行模板命令: {subcommand}")
            logger.debug(f"命令参数: {args}")
            handler(args)
        except Exception as e:
            logger.exception(f"执行模板命令 {subcommand} 时发生错误")
            console.print(f"[bold red]错误: {str(e)}[/bold red]")
            sys.exit(1)
    else:
        console.print(f"[bold red]错误: 未知的模板子命令 {subcommand}[/bold red]")
        sys.exit(1)


def main():
    """
    模板命令行主入口
    """
    parser = argparse.ArgumentParser(description="模板管理和生成工具")
    subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

    # 注册模板命令
    register_template_commands(subparsers)

    # 解析命令行参数
    args = parser.parse_args()

    # 如果没有提供子命令，显示帮助信息
    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    # 执行命令
    execute_template_command(args)


if __name__ == "__main__":
    main()
