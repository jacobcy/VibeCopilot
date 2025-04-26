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


@click.command(name="create", help="创建或导入工作流定义")
@click.option("--source", help="从描述性文本创建时指定源文件路径")
@click.option("--template", default="templates/flow/default_flow.json", help="从源文件创建时使用的工作流模板路径")
@click.option("--import_path", help="从文件导入工作流定义，与 --source/--template 互斥")
@click.option("--name", "-n", help="工作流名称（创建或导入时均可指定）")
@click.option("--output", "-o", help="输出工作流文件路径（仅在从 source 创建时有效）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def create(source: Optional[str], template: str, import_path: Optional[str], name: Optional[str], output: Optional[str], verbose: bool) -> None:
    """
    创建或导入工作流定义。

    - **从源文件创建**: 使用 `--source` 指定描述性文本文件，并可选 `--template`。
    - **从文件导入**: 使用 `--import_path` 指定包含工作流定义的 JSON 文件。

    `--source` 和 `--import_path` 选项是互斥的。

    示例:
      vc flow create --source story.md                  # 从 story.md 创建
      vc flow create --import_path existing_flow.json   # 从 existing_flow.json 导入
      vc flow create --import_path wf.json --name "新流程" # 导入并重命名
    """
    try:
        # Check for mutually exclusive options
        if source and import_path:
            console.print("[red]错误: --source 和 --import_path 选项不能同时使用。[/red]")
            return
        if not source and not import_path:
            console.print("[red]错误: 必须提供 --source 或 --import_path 中的一个选项。[/red]")
            return
        if import_path and output:
            console.print("[yellow]警告: --output 选项在导入模式下无效，将被忽略。[/yellow]")
            output = None  # Ensure output is ignored in import mode

        if verbose:
            if import_path:
                console.print(f"正在从 {import_path} 导入工作流定义...")
            else:
                console.print("正在创建工作流定义...")

        # Prepare arguments for the handler
        handler_args = {
            "source": source,
            "template": template,
            "import_path": import_path,
            "name": name,
            "output": output,
            "verbose": verbose,
            "_agent_mode": False,
        }

        # 调用处理函数并等待结果
        result: Dict[str, Any] = asyncio.run(handle_create_subcommand(handler_args))

        if result["status"] == "success":
            if verbose:
                mode = "导入" if import_path else "创建"
                console.print(f"[green]成功{mode}工作流定义[/green]")
            console.print(result["message"])
        else:
            console.print(f"[red]错误: {result['message']}[/red]")

    except Exception as e:
        logger.error(f"创建或导入工作流定义失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")


@click.command(name="update", help="更新工作流定义")
@click.argument("id")
@click.option("--name", help="新的工作流名称")
@click.option("--desc", "--desc", help="新的工作流描述")
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
