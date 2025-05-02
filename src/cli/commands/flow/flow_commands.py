"""
工作流命令模块

提供工作流创建、管理和执行的命令接口。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console

# 从flow_crud_commands模块导入CRUD命令
from src.cli.commands.flow.flow_crud_commands import create, delete, export, update

# 保留其他处理程序的导入
from src.cli.commands.flow.handlers.list import handle_list_subcommand
from src.cli.commands.flow.handlers.show import handle_show_subcommand

# 从flow_info模块导入处理函数
# Removed context and next handlers
# from src.cli.commands.flow.handlers.flow_info import handle_context_subcommand, handle_next_subcommand


console = Console()
logger = logging.getLogger(__name__)


def register_basic_commands(flow_group):
    """向主命令组注册基本命令"""

    @flow_group.command(name="list", help="列出所有工作流定义")
    @click.option("-t", "--type", "workflow_type", help="按工作流类型筛选")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    # 使用pass_service装饰器注入FlowService实例
    # ServiceFactory会根据service_type创建对应的服务实例
    def list_flow(workflow_type: Optional[str], verbose: bool) -> None:
        """列出所有工作流定义"""
        try:
            if verbose:
                console.print("正在获取工作流列表...")

            # 调用处理函数
            result: Dict[str, Any] = handle_list_subcommand({"workflow_type": workflow_type, "verbose": verbose, "_agent_mode": False})

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取工作流列表[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            logger.error(f"列出工作流失败: {e}", exc_info=True)
            console.print(f"[red]错误: {str(e)}[/red]")

    @flow_group.command(name="show", help="查看工作流定义详情")
    @click.argument("id")  # ID now only refers to workflow ID
    @click.option("--format", "-f", type=click.Choice(["mermaid", "yaml"]), default="yaml", help="输出格式")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
    def show(id: str, format: str, verbose: bool) -> None:
        """
        查看工作流定义详情。

        接受工作流ID (例如 'wf_dev_process')。

        示例:
          vc flow show wf_dev_process            # 默认使用YAML格式
          vc flow show wf_dev_process -f yaml    # 使用YAML格式
          vc flow show wf_dev_process -f mermaid # 显示工作流图表
        """
        try:
            if not id.startswith("wf_"):
                console.print("[yellow]警告: ID 似乎不是标准工作流ID (应以 'wf_' 开头)。[/yellow]")
                # Proceed anyway, handler might still work if ID is valid workflow ID

            if verbose:
                console.print(f"正在获取工作流 '{id}' 的详情...")

            # Call the handler (assuming it primarily handles workflows now)
            # 如果格式是 mermaid，自动设置 diagram 为 True，否则为 False
            diagram = format == "mermaid"
            result = handle_show_subcommand(
                {
                    "id": id,
                    "format": format,
                    "diagram": diagram,
                    "verbose": verbose,
                    "_agent_mode": False,
                }
            )

            if result["status"] == "success":
                if verbose:
                    console.print("[green]成功获取详情[/green]")
                console.print(result["message"])
            else:
                console.print(f"[red]错误: {result['message']}[/red]")

        except Exception as e:
            console.print(f"[red]错误: {str(e)}[/red]")


# 注册命令 (移除 session 和 flow group 定义)
# register_basic_commands(flow) # This function is called in flow_click.py
# flow.add_command(session) # Removed
# flow.add_command(create) # These are added in flow_click.py
# flow.add_command(update) # These are added in flow_click.py
# flow.add_command(delete) # These are added in flow_click.py
# flow.add_command(export) # These are added in flow_click.py
