"""
状态命令模块

提供查询和管理系统状态的命令实现，使用Click框架
"""

import logging
from typing import Optional

import click
from rich.console import Console

from src.cli.commands.status.output_helpers import output_result

# 导入我们的新命令
from src.cli.commands.status.subcommands.init import init_command
from src.cli.core.decorators import pass_service

# 引入 get_config
from src.core.config import get_config
from src.status import StatusService

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="status")
def status():
    """项目状态管理相关命令"""
    logger.info("Status command group invoked.")
    pass


@status.command(name="show")
@click.option("--entity-type", help="实体类型", default=None)
@click.option("--entity-id", help="实体ID", default=None)
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def show_command(entity_type, entity_id, format, verbose):
    """显示项目状态信息"""
    from src.cli.commands.status.subcommands.show import handle_show

    handle_show(None, {"entity_type": entity_type, "entity_id": entity_id, "format": format, "verbose": verbose})


@status.command(name="roadmap", help="显示路线图状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
def roadmap(verbose=False, format="text"):
    """显示路线图状态"""
    logger.info("Roadmap command function entered.")
    service = None
    try:
        logger.info("Attempting to get StatusService instance manually.")
        service = StatusService.get_instance()
        logger.info(f"StatusService instance obtained manually: {service}")
    except Exception as e_service_init:
        logger.error(f"Error getting StatusService instance: {e_service_init}", exc_info=True)
        error_msg_init = str(e_service_init) if str(e_service_init) else repr(e_service_init)
        if not error_msg_init or error_msg_init == "None":
            error_msg_init = "获取 StatusService 实例时发生未知错误。"
        console.print(f"[bold red]初始化错误:[/bold red] {error_msg_init}")
        return 1

    if verbose:
        logger.info("Executing 'vc status roadmap --verbose'")
        logger.info(f"StatusService instance: {service}")
        if service and hasattr(service, "provider_manager"):
            logger.info(f"ProviderManager instance: {service.provider_manager}")
            roadmap_provider = service.provider_manager.get_provider("roadmap")
            logger.info(f"Roadmap provider from manager: {roadmap_provider}")
            if roadmap_provider:
                logger.info(f"Type of roadmap provider: {type(roadmap_provider)}")
        else:
            logger.warning("StatusService (manual) or ProviderManager not available.")

    try:
        if not service:
            logger.error("Service is None before calling get_domain_status.")
            console.print("[bold red]执行错误:[/bold red] 状态服务未能初始化。")
            return 1

        if verbose:
            logger.info('Calling service.get_domain_status("roadmap")')
        result = service.get_domain_status("roadmap")
        if verbose:
            logger.info(f"Result from get_domain_status: {result}")

        output_result(result, format, "domain", verbose)
    except Exception as e:
        error_message = str(e) if str(e) else repr(e)
        if not error_message or error_message == "None":
            error_message = "执行 roadmap 状态命令时发生未知错误。请检查日志以获取详细信息。"
        console.print(f"[bold red]执行错误:[/bold red] {error_message}")
        logger.error(f"Error executing 'vc status roadmap': {e}", exc_info=True)
        return 1


@status.command(name="task", help="显示任务状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def task(service, verbose=False, format="text"):
    """显示任务状态"""
    try:
        # 直接调用服务获取任务状态
        result = service.get_domain_status("task")

        # 如果是文本格式且存在当前任务，显示当前任务信息
        if format == "text" and isinstance(result, dict):
            if "current_task" in result and result["current_task"]:
                current = result["current_task"]
                console.print("\n[bold green]当前活动任务:[/bold green]")
                console.print(f"  ID: [cyan]{current['id']}[/cyan]")
                console.print(f"  标题: {current['title']}")
                console.print(f"  状态: [yellow]{current['status']}[/yellow]")
                if current.get("priority"):
                    console.print(f"  优先级: {current['priority']}")
                if current.get("assignee"):
                    console.print(f"  负责人: {current['assignee']}")

                console.print("\n要查看完整任务详情，请运行: [bold]vc task show[/bold]\n")
            else:
                console.print("\n[bold yellow]当前没有活动任务[/bold yellow]")
                console.print("要设置当前任务，请运行: [bold]vc task current <任务ID>[/bold]\n")

        # 输出结果（总体状态信息）
        output_result(result, format, "task", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@status.command(name="update", help="更新项目阶段")
@click.option("--phase", required=True, help="项目阶段")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def update(service, phase, verbose=False, format="text"):
    """更新项目阶段"""
    try:
        # 直接调用服务更新项目阶段
        result = service.update_project_phase(phase)

        # 输出结果
        output_result(result, format, "generic", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


# 注册新的init命令
status.add_command(init_command)


if __name__ == "__main__":
    status()
