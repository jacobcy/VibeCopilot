"""
工作流命令主模块 (Click 版本)

提供工作流相关命令的主入口点和通用功能。
"""

import logging

import click
from rich.console import Console

# 导入子命令模块
from src.cli.commands.flow.commands.flow_basic_commands import register_basic_commands
from src.cli.commands.flow.commands.flow_create_commands import create
from src.cli.commands.flow.commands.flow_session_commands import session
from src.cli.decorators import pass_service
from src.workflow.service.flow_service import FlowService

console = Console()
logger = logging.getLogger(__name__)


@click.group(help="管理和执行工作流")
def flow():
    """
    工作流管理命令组

    此命令组用于管理工作流定义和执行工作流会话。

    主要子命令:

    - flow create: 创建工作流定义
      用法: flow create --source <文件路径>

    - flow session create: 创建并启动工作会话
      用法: flow session create --workflow <工作流ID>

    - flow session list: 列出工作会话
    - flow session show: 查看会话详情
    - flow session pause/resume: 暂停/恢复会话
    """
    pass


# 注册子命令组
flow.add_command(session)
flow.add_command(create)

# 注册基本命令
register_basic_commands(flow)

# 导出
__all__ = ["flow"]


@flow.command(name="validate", help="验证工作流文件一致性，确保ID与文件名匹配")
@click.option("--fix", is_flag=True, help="自动修复文件一致性问题")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="flow")
def validate_flow(service: FlowService, fix: bool, verbose: bool) -> None:
    """验证工作流文件一致性"""
    try:
        console.print("正在验证工作流文件一致性...")

        # 调用验证函数
        from src.workflow.workflow_operations import validate_workflow_files

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
