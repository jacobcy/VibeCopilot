"""
VibeCopilot命令行界面主程序

提供CLI命令行接口，允许用户通过命令行与VibeCopilot交互
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.cli.commands import add_db_commands, add_template_commands, handle_db_command, handle_template_command

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def setup_arg_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="VibeCopilot命令行工具")
    parser.add_argument("--verbose", "-v", action="store_true", help="启用详细日志输出")
    parser.add_argument("--quiet", "-q", action="store_true", help="只显示错误和警告")
    parser.add_argument("--config", help="指定配置文件路径")

    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 添加数据库命令
    add_db_commands(subparsers)

    # 添加模板命令
    add_template_commands(subparsers)

    # 添加其他命令...
    # TODO: 随着功能扩展，添加更多命令类型

    return parser


def configure_logging(args):
    """配置日志级别"""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("已启用详细日志输出")
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)


def main():
    """主函数"""
    # 设置参数解析器
    parser = setup_arg_parser()

    # 解析命令行参数
    args = parser.parse_args()

    # 配置日志级别
    configure_logging(args)

    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return 0

    # 根据命令分发到相应的处理函数
    try:
        if args.command == "db":
            return handle_db_command(args)
        elif args.command == "template":
            return handle_template_command(args)
        elif hasattr(args, "func"):
            # 直接调用设置的处理函数
            return args.func(args)
        else:
            logger.error(f"未知命令: {args.command}")
            parser.print_help()
            return 1
    except Exception as e:
        logger.exception(f"命令执行失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
