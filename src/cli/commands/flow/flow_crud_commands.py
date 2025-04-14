"""
工作流CRUD命令模块

提供工作流定义的创建、更新、删除、导入和导出等操作的命令实现。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import click
from rich.console import Console

from src.cli.commands.flow.handlers.flow_crud import handle_create_subcommand, handle_delete_subcommand, handle_update_subcommand
from src.cli.commands.flow.handlers.flow_io import handle_export_subcommand, handle_import_subcommand

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="create", help="创建工作流定义")
@click.option("--source", required=True, help="源文件路径，可以是任何描述性的文本文件")
@click.option("--template", default="templates/flow/default_flow.json", help="工作流模板路径，默认使用templates/flow/default_flow.json")
@click.option("--name", "-n", help="工作流名称")
@click.option("--output", "-o", help="输出工作流文件路径（可选）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def create(source: str, template: str, name: Optional[str], output: Optional[str], verbose: bool) -> None:
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
        result: Dict[str, Any] = asyncio.run(
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


@click.command(name="update", help="更新工作流定义")
@click.argument("id")
@click.option("--name", help="新的工作流名称")
@click.option("--desc", "--description", help="新的工作流描述")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def update(id: str, name: Optional[str], description: Optional[str], verbose: bool) -> None:
    """
    更新工作流定义

    修改现有工作流定义的名称或描述等基本信息。

    示例:
      vc flow update dev --name "新开发流程"             # 更新工作流名称
      vc flow update dev --desc "优化的开发流程定义"      # 更新工作流描述
    """
    try:
        if verbose:
            console.print(f"正在更新工作流 {id}...")

        # 调用处理函数
        result: Dict[str, Any] = handle_update_subcommand(
            {"id": id, "name": name, "description": description, "verbose": verbose, "_agent_mode": False}
        )

        if result["status"] == "success":
            if verbose:
                console.print("[green]成功更新工作流[/green]")
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"更新工作流失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@click.command(name="delete", help="删除工作流定义")
@click.argument("workflow_id")
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def delete(workflow_id: str, force: bool, verbose: bool) -> None:
    """
    删除工作流定义

    永久删除指定的工作流定义及相关数据。

    示例:
      vc flow delete dev                # 删除ID为dev的工作流
      vc flow delete dev --force        # 强制删除，不提示确认
    """
    try:
        if verbose:
            console.print(f"正在删除工作流 {workflow_id}...")

        # 调用处理函数
        result: Dict[str, Any] = handle_delete_subcommand({"workflow_id": workflow_id, "force": force, "verbose": verbose, "_agent_mode": False})

        if result["status"] == "success":
            if verbose:
                console.print("[green]成功删除工作流[/green]")
            console.print(result["message"])
        elif result["status"] == "cancelled":
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"删除工作流失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@click.command(name="export", help="导出工作流定义")
@click.argument("workflow_id")
@click.option("--format", "-f", type=click.Choice(["json", "mermaid"]), default="json", help="导出格式")
@click.option("--output", "-o", help="输出文件路径")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def export(workflow_id: str, format: str, output: Optional[str], verbose: bool) -> None:
    """
    导出工作流定义

    将工作流定义导出为JSON或Mermaid格式。

    示例:
      vc flow export dev                     # 导出为JSON格式
      vc flow export dev --format mermaid    # 导出为Mermaid格式
      vc flow export dev -o workflow.json    # 导出到指定文件
    """
    try:
        if verbose:
            console.print(f"正在导出工作流 {workflow_id}...")

        # 调用处理函数
        result: Dict[str, Any] = handle_export_subcommand(
            {"workflow_id": workflow_id, "format": format, "output": output, "verbose": verbose, "_agent_mode": False}
        )

        if result["status"] == "success":
            if verbose:
                console.print("[green]成功导出工作流[/green]")
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"导出工作流失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@click.command(name="import", help="导入工作流定义（同名工作流将自动替换）")
@click.argument("file_path")
@click.option("--name", help="导入后使用的工作流名称，如不提供则使用原名称")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def import_flow(file_path: str, name: Optional[str], verbose: bool) -> None:
    """
    导入工作流定义

    从JSON文件导入工作流定义。同名工作流将被替换。

    示例:
      vc flow import workflow.json           # 导入工作流
      vc flow import workflow.json --name dev # 导入并重命名
    """
    try:
        if verbose:
            console.print(f"正在导入工作流文件 {file_path}...")

        # 调用处理函数
        result: Dict[str, Any] = handle_import_subcommand({"file_path": file_path, "name": name, "verbose": verbose, "_agent_mode": False})

        if result["status"] == "success":
            if verbose:
                console.print("[green]成功导入工作流[/green]")
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"导入工作流失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")
