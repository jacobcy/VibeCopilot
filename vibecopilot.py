"""
VibeCopilot命令行界面主程序

提供CLI命令行接口，允许用户通过命令行与VibeCopilot交互
"""

import logging
import os
import sys
from pathlib import Path

import click

from src.cli.commands import CLICK_COMMANDS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="启用详细日志输出")
@click.option("--quiet", "-q", is_flag=True, help="只显示错误和警告")
@click.option("--config", help="指定配置文件路径")
@click.pass_context
def cli(ctx, verbose, quiet, config):
    """VibeCopilot命令行工具"""
    # 配置日志级别
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("已启用详细日志输出")
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # 存储配置信息
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


def main():
    """主函数"""
    # 添加所有Click命令
    for command in CLICK_COMMANDS:
        cli.add_command(command)

    # 运行CLI
    return cli()


if __name__ == "__main__":
    sys.exit(main())
