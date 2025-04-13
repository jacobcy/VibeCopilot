"""
状态命令模块 (Click 版本)

提供查询和管理系统状态的命令实现，使用Click框架
"""

import logging
from typing import Optional

import click
from rich.console import Console

from src.cli.commands.status.output_helpers import output_result
from src.cli.decorators import pass_service
from src.status import StatusService

console = Console()
logger = logging.getLogger(__name__)


@click.group(help="项目状态管理命令")
def status():
    """项目状态管理命令组"""
    pass


@status.command(name="show", help="显示项目状态概览")
@click.option(
    "--type",
    type=click.Choice(["all", "summary", "critical"]),
    default="summary",
    help="状态类型",
)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def show(service, type="summary", verbose=False, format="text"):
    """显示项目状态概览"""
    try:
        # 获取基本系统状态
        if type == "all":
            result = service.get_system_status(detailed=True)
        elif type == "critical":
            result = service.get_critical_status()
        else:  # summary
            result = service.get_system_status(detailed=False)

        # 获取任务摘要
        try:
            task_summary = service.get_domain_status("task")
            task_summary.pop("error", None)
            result["task_summary"] = task_summary
        except Exception as task_e:
            logger.warning(f"获取任务摘要时出错: {task_e}")
            result["task_summary"] = {"error": f"获取任务摘要失败: {task_e}"}

        # 输出结果
        output_result(result, format, "system", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@status.command(name="flow", help="显示流程状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def flow(service, verbose=False, format="text"):
    """显示流程状态"""
    try:
        # 直接调用服务获取流程状态
        result = service.get_domain_status("flow")

        # 输出结果
        output_result(result, format, "domain", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@status.command(name="roadmap", help="显示路线图状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def roadmap(service, verbose=False, format="text"):
    """显示路线图状态"""
    try:
        # 直接调用服务获取路线图状态
        result = service.get_domain_status("roadmap")

        # 输出结果
        output_result(result, format, "domain", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
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

        # 输出结果
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


@status.command(name="init", help="初始化项目状态")
@click.option("--name", help="项目名称")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def init(service, name=None, verbose=False, format="text"):
    """初始化项目状态"""
    try:
        # 设置默认项目名称
        project_name = name if name else "VibeCopilot"

        # 在开始时输出初始化标记
        if format == "text":
            console.print(f"🚀 [bold]正在初始化项目状态...[/bold]")

        # 直接调用服务初始化项目状态
        result = service.initialize_project_status(project_name)

        if format == "text" and "status" in result and result["status"] == "success":
            console.print(f"✅ [bold green]初始化完成[/bold green]: 项目 {project_name} 状态已初始化")

        # 输出结果
        output_result(result, format, "generic", verbose)
    except Exception as e:
        console.print(f"[bold red]初始化错误:[/bold red] {str(e)}")
        return 1


if __name__ == "__main__":
    status()
