"""
工作流命令主模块

提供工作流相关命令的主入口点和通用功能。
"""

import logging

import click
from rich.console import Console

# 导入子命令模块和命令
from src.cli.commands.flow.flow_commands import register_basic_commands
from src.cli.commands.flow.flow_crud_commands import create, delete, export, update
from src.cli.commands.flow.session_commands import session
from src.cli.core.groups import FormattedHelpGroup  # Import the custom group class

console = Console()
logger = logging.getLogger(__name__)


@click.group(cls=FormattedHelpGroup)  # Use the custom group class
def flow():
    """
    管理和执行 VibeCopilot 工作流。

    提供工作流定义管理和工作流会话执行相关的功能。
    使用下面的命令可以查看不同分组的具体操作。
    """
    pass


# 注册子命令组
flow.add_command(session)

# 注册CRUD命令
flow.add_command(create)
flow.add_command(update)
flow.add_command(delete)
flow.add_command(export)

# 注册基本命令
register_basic_commands(flow)

# 注册别名命令 - run 作为 session create 的别名
from src.cli.commands.flow.session_commands import create_session

flow.add_command(create_session, name="run")

# 导出
__all__ = ["flow"]


@flow.command(name="validate", help="验证工作流文件一致性，确保ID与文件名匹配")
@click.option("--fix", is_flag=True, help="自动修复文件一致性问题")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def validate_flow(fix: bool, verbose: bool) -> None:
    """验证工作流文件一致性"""
    try:
        console.print("正在验证工作流文件一致性...")

        # 调用验证函数
        from src.workflow.service import validate_workflow_files

        result = validate_workflow_files(auto_fix=fix)

        # 显示验证结果
        console.print(f"\n[bold cyan]验证结果:[/bold cyan]")
        console.print(f"有效文件数: [green]{result['valid']}[/green]")

        if result["invalid"] > 0:
            if result["fixed"] > 0:
                console.print(f"无效文件数: [yellow]{result['invalid']}[/yellow]")
                console.print(f"已修复文件数: [green]{result['fixed']}[/green]")
            else:
                console.print(f"无效文件数: [red]{result['invalid']}[/red]")
                if not fix:
                    console.print("使用 --fix 选项自动修复问题")
        else:
            console.print("所有工作流文件均有效，无需修复")

        # 如果启用了详细输出，显示所有文件的状态
        if verbose:
            console.print("\n[bold cyan]详细信息:[/bold cyan]")
            for detail in result["details"]:
                status = detail["status"]
                if status == "valid":
                    console.print(f"[green]✓[/green] {detail['file']} (ID: {detail['id']})")
                elif status == "fixed":
                    console.print(f"[yellow]✓[/yellow] {detail['file']} - 已修复: {detail['issue']}")
                else:
                    console.print(f"[red]✗[/red] {detail['file']} - 问题: {detail['issue']}")

    except Exception as e:
        logger.error(f"验证工作流文件失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")
