"""
状态命令模块

提供查询和管理系统状态的命令实现，使用Click框架
"""

import logging
from typing import Optional

import click
from rich.console import Console

from src.cli.commands.status.output_helpers import output_result
from src.cli.decorators import pass_service

# 引入 get_config
from src.core.config import get_config
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
def show(service: StatusService, type="summary", verbose=False, format="text"):
    """显示项目状态概览"""
    try:
        config_manager = get_config()
        app_name = config_manager.get("app.name", "VibeCopilot")  # 获取应用名称

        # 获取基本系统状态
        if type == "all":
            result = service.get_system_status(detailed=True)
        elif type == "critical":
            result = service.get_critical_status()
        else:  # summary
            result = service.get_system_status(detailed=False)

        # 将应用名称添加到结果中以便输出
        if isinstance(result, dict):
            # 确保 system_info 存在
            if "system_info" not in result:
                result["system_info"] = {}
            result["system_info"]["app_name"] = app_name

        # 获取任务摘要
        try:
            task_summary = service.get_domain_status("task")
            task_summary.pop("error", None)
            result["task_summary"] = task_summary
        except Exception as task_e:
            logger.warning(f"获取任务摘要时出错: {task_e}")
            result["task_summary"] = {"error": f"获取任务摘要失败: {task_e}"}

        # 输出结果
        if format == "text":
            console.print(f"[bold cyan]=== {app_name} 状态概览 ===[/bold cyan]\n")

        output_result(result, format, "system", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@status.command(name="workflow", help="显示工作流状态")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def workflow(service, verbose=False, format="text"):
    """显示工作流状态"""
    try:
        # 直接调用服务获取工作流状态
        result = service.get_domain_status("workflow")

        # 输出结果
        output_result(result, format, "domain", verbose)
    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@status.command(name="flow", help="显示工作流状态 (workflow的别名)")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@pass_service(service_type="status")
def flow(service, verbose=False, format="text"):
    """显示工作流状态 (workflow的别名)"""
    try:
        # 使用实体ID "current" 获取当前会话工作流状态
        result = service.get_domain_status("workflow", entity_id="current")

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
