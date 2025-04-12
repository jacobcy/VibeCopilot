"""
工作流创建命令模块 (Click 版本)

提供工作流定义创建命令的实现。
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.commands.flow.handlers.create_handler import handle_create_subcommand
from src.cli.decorators import pass_service
from src.workflow.service.flow_service import FlowService

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="create", help="创建工作流定义")
@click.option("--source", required=True, help="源文件路径，可以是任何描述性的文本文件")
@click.option("--template", default="templates/flow/default_flow.json", help="工作流模板路径，默认使用templates/flow/default_flow.json")
@click.option("--name", "-n", help="工作流名称")
@click.option("--output", "-o", help="输出工作流文件路径（可选）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="flow")
def create(service: FlowService, source: str, template: str, name: Optional[str], output: Optional[str], verbose: bool) -> None:
    """
    创建工作流定义

    从描述性文本文件创建工作流定义，使用LLM进行解析。

    示例:
      vc flow create --source story.md                  # 从story.md创建工作流定义
      vc flow create --source story.md --name "开发流程" # 创建指定名称的工作流定义
    """
    try:
        # 创建工作流定义
        if verbose:
            console.print("正在创建工作流定义...")

        # 调用处理函数并等待结果
        result = asyncio.run(
            handle_create_subcommand(
                {"source": source, "template": template, "name": name, "output": output, "verbose": verbose, "_agent_mode": False}
            )
        )

        if result["status"] == "success":
            if verbose:
                console.print("[green]成功创建工作流定义[/green]")
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"创建工作流定义失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")
