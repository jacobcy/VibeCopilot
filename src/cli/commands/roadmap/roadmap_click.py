"""
路线图管理命令模块

处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import asyncio
import logging
from functools import wraps
from typing import Optional

import click
from rich.console import Console

from src.cli.commands.roadmap.handlers.delete_handlers import get_object_name, get_type_name, handle_delete
from src.cli.commands.roadmap.handlers.import_handlers import handle_import
from src.cli.commands.roadmap.handlers.list_handlers import handle_list_roadmaps
from src.cli.commands.roadmap.handlers.show_handlers import handle_show_all_milestones, handle_show_elements_by_type, handle_show_roadmap
from src.cli.commands.roadmap.handlers.switch_handlers import handle_switch_roadmap
from src.cli.core.decorators import pass_service

console = Console()
logger = logging.getLogger(__name__)


def async_command(f):
    """装饰器：将异步命令转换为同步命令"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group(help="路线图管理命令")
def roadmap():
    """路线图管理命令组"""
    pass


@roadmap.command(name="sync", help="从GitHub同步路线图数据")
@click.argument("repository", required=True)
@click.option("--theme", "-t", help="GitHub项目主题标签")
@click.option(
    "--operation",
    "-o",
    type=click.Choice(["push", "pull"]),
    default="pull",
    help="同步操作类型",
)
@click.option("--roadmap", "-r", help="指定路线图ID")
@click.option("--force", "-f", is_flag=True, help="强制同步，忽略冲突")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
@pass_service
def sync(
    service,
    repository,
    theme=None,
    operation="pull",
    roadmap=None,
    force=False,
    verbose=False,
):
    """从GitHub同步路线图数据

    REPOSITORY: GitHub仓库名称，格式：所有者/仓库名
    """
    from .handlers.sync_handlers import RoadmapSyncHandlers

    sync_args = {
        "repository": repository,
        "theme": theme,
        "operation": operation,
        "roadmap": roadmap,
        "force": force,
        "verbose": verbose,
    }

    try:
        result = RoadmapSyncHandlers.handle_sync_command(sync_args, service)

        if verbose:
            console.print(f"[bold]完整响应:[/]\n{result}")
        else:
            status_icon = "✓" if result.get("status") == "success" else "✗"
            color = "green" if result.get("status") == "success" else "red"
            console.print(f"[{color}]{status_icon} {result.get('summary', 'GitHub同步完成')}[/{color}]")
    except Exception as e:
        console.print(f"[red]✗ GitHub同步失败: {str(e)}[/red]")


@roadmap.command(name="switch", help="切换活动路线图")
@click.argument("roadmap_id", required=False)
@click.option("--show", is_flag=True, help="只显示当前活动路线图")
@click.option("--clear", is_flag=True, help="清除当前活动路线图设置")
@pass_service
def switch(service, roadmap_id=None, show=False, clear=False):
    """切换活动路线图

    ROADMAP_ID: 路线图ID，不提供则显示当前活动路线图
    """
    try:
        result = handle_switch_roadmap(service, roadmap_id, show, clear)

        if result.get("success"):
            console.print(f"[green]{result.get('message')}[/green]")
            return 0
        else:
            console.print(f"[red]{result.get('message')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        return 1


@roadmap.command(name="list", help="列出路线图")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service
def list_roadmaps(
    service,
    verbose=False,
):
    """列出所有路线图"""
    try:
        # 列出所有路线图
        result = handle_list_roadmaps(service=service, verbose=verbose)

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '获取路线图列表失败')}[/red]")
            return 1

        # 输出结果
        console.print(result.get("formatted_output", ""), highlight=False)

        # 总数已经在 format_roadmaps_output 中显示，这里不需要重复显示

        return 0

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="create", help="创建新的路线图元素或从文件生成标准YAML")
@click.argument("type", type=click.Choice(["milestone", "epic", "story"]), required=False)
@click.argument("title", required=False)
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True, dir_okay=False),
    help="用于生成路线图YAML的源文件 (Markdown或YAML)",
)
@click.option("--epic", "-e", help="所属史诗ID (用于story, 手动创建时)")
@click.option("--desc", "-d", help="详细描述 (手动创建时)")
@click.option("--assignee", "-a", help="指派给用户 (手动创建时)")
@click.option("--labels", "-l", help="标签列表，用逗号分隔 (手动创建时)")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["high", "medium", "low"]),
    help="优先级 (用于epic, 手动创建时)",
)
@pass_service
@async_command
async def create(
    service,
    source: Optional[str],
    type: Optional[str],
    title: Optional[str],
    epic: Optional[str],
    desc: Optional[str],
    assignee: Optional[str],
    labels: Optional[str],
    priority: Optional[str] = None,
):
    """创建新的路线图元素或从源文件生成标准路线图YAML。

    使用 --source 时:
        - 从源文件 (Markdown或YAML) 解析路线图结构。
        - 在源文件相同目录下，生成一个同名但扩展名为.yaml的标准格式文件。
        - 不会直接在系统中创建元素，需使用 'vc roadmap import' 导入生成的YAML。
        - 将忽略 type, title, epic, desc, assignee, labels, priority 参数。

    不使用 --source 时:
        - 必须提供 type 和 title 参数手动创建单个元素。
        - 可以使用 --epic, --desc, --assignee, --labels, --priority 提供细节。
    """
    from .handlers.create_handlers import handle_create_element, handle_create_from_source

    try:
        if source:
            # --- 处理从文件生成 YAML ---
            if type or title:
                console.print("[yellow]警告: 使用 --source 时，将忽略 type, title 及其他手动创建参数。[/yellow]")

            # 调用处理函数，接收包含解析数据的字典
            result = await handle_create_from_source(service=service, source=source)

            # --- 恢复处理 output_file 的逻辑 ---
            if result.get("success"):
                console.print(f"[green]{result.get('message')}[/green]")
                # 更新提示信息，引用自动生成的文件路径
                if result.get("output_file"):
                    console.print(f"[cyan]下一步: 使用 'vc roadmap import {result.get('output_file')}' 导入生成的路线图。[/cyan]")
                return 0
            else:
                # 处理解析失败的情况
                console.print(f"[bold red]处理源文件失败: {result.get('message', '未知错误')}[/bold red]")
                error_details = result.get("error_details")
                if error_details:
                    console.print(f"错误详情: {str(error_details)[:500]}...")  # 打印部分错误详情
                return 1
        elif type and title:
            # --- 处理手动创建单个元素 ---
            result = handle_create_element(
                service=service,
                type=type,
                title=title,
                epic_id=epic,
                description=desc,
                assignee=assignee,
                labels=labels.split(",") if labels else None,
                priority=priority,
            )
            if result.get("success"):
                console.print(f"[green]{result['message']}[/green]")
                # 可以在这里打印创建的元素ID等信息
                if result.get("data"):
                    console.print(f"元素详情: ID={result['data'].get('id')}, Title='{result['data'].get('title')}'")
                return 0
            else:
                console.print(f"[bold red]创建元素失败: {result.get('message', '未知错误')}[/bold red]")
                return 1
        else:
            # --- 无效的参数组合 ---
            console.print("[red]错误: 必须提供 --source 选项或同时提供 type 和 title 参数。[/red]")
            ctx = click.get_current_context()
            console.print(ctx.get_help())
            return 1

    except Exception as e:
        console.print(f"[bold red]执行 create 命令时出错: {str(e)}[/bold red]")
        # Consider logging the full traceback here
        # import traceback
        # logger.error(f"Error during create command: {traceback.format_exc()}")
        return 1


@roadmap.command(name="update", help="更新路线图元素状态")
@click.argument("type", type=click.Choice(["milestone", "epic", "story"]))
@click.argument("id")
@click.argument("status")
@click.option("--comment", "-c", help="更新说明")
@click.option("--desc", "-d", help="详细描述")
@click.option("--assignee", "-a", help="更新指派人")
@click.option("--labels", "-l", help="更新标签（用逗号分隔）")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["high", "medium", "low"]),
    help="优先级 (用于epic)",
)
@pass_service
def update(
    service,
    type: str,
    id: str,
    status: str,
    comment: Optional[str] = None,
    desc: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    priority: Optional[str] = None,
):
    """更新路线图元素状态"""
    from .handlers.update_handlers import RoadmapUpdateHandlers

    update_args = {
        "type": type,
        "id": id,
        "status": status,
        "comment": comment,
        "desc": desc,
        "assignee": assignee,
        "labels": labels,
        "priority": priority,
    }

    try:
        result = RoadmapUpdateHandlers.handle_update_command(update_args, service)

        if result.get("status") == "success":
            console.print(f"[green]✓ {result.get('message')}[/green]")
            return 0
        else:
            console.print(f"[red]✗ {result.get('message', '更新失败')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="validate", help="验证路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service
@async_command
async def validate(
    service,
    source: str,
    verbose: bool = False,
):
    """验证路线图YAML文件格式"""
    from src.validation.roadmap_validation import RoadmapValidator

    try:
        # 创建验证器
        validator = RoadmapValidator()

        # 验证文件
        is_valid, warnings, errors = validator.validate_file(source)

        # 显示验证结果
        if is_valid and not warnings and not errors:
            console.print("[bold green]✅ 验证通过，文件格式完全符合要求[/bold green]")
            return 0

        # 显示警告
        if warnings:
            console.print("\n[bold yellow]警告:[/bold yellow]")
            for warning in warnings:
                console.print(f"[yellow]⚠️ {warning}[/yellow]")

        # 显示错误
        if errors:
            console.print("\n[bold red]错误:[/bold red]")
            for error in errors:
                console.print(f"[red]❌ {error}[/red]")

        # 返回状态码
        return 0 if is_valid else 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        if verbose:
            console.print("[red]详细错误信息:[/red]")
            import traceback

            console.print(traceback.format_exc())
        return 1


@roadmap.command(name="import", help="导入路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--activate", "-a", is_flag=True, help="导入后设为当前活动路线图")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service
@async_command
async def import_roadmap(
    service,
    source: str,
    activate: bool,
    verbose: bool,
):
    """从YAML文件导入路线图"""
    try:
        # 调用导入处理器，不传递roadmap_id和fix参数
        result = await handle_import(source, service, None, False, activate, verbose)

        # 处理警告
        if result.get("warnings"):
            for warning in result["warnings"]:
                console.print(f"[yellow]警告: {warning}[/yellow]")

        # 处理结果
        if result.get("success"):
            roadmap_id = result.get("roadmap_id")
            console.print(f"[green]导入成功: 路线图ID {roadmap_id}[/green]")

            if result.get("activated"):
                console.print(f"[green]已设置 {roadmap_id} 为活动路线图[/green]")

            return 0
        else:
            console.print(f"[red]{result.get('error', '导入失败')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        return 1


@roadmap.command(name="show", help="查看路线图详情")
@click.option("--id", "-i", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--type", "-t", type=click.Choice(["roadmap", "milestone", "epic", "story"]), default="roadmap", help="要显示的元素类型")
@pass_service
def show(service, id=None, type="roadmap"):
    """查看路线图详情"""
    try:
        # 获取路线图ID
        roadmap_id = id or service.active_roadmap_id
        if not roadmap_id:
            console.print("[red]未指定路线图ID，且未设置活动路线图。请指定ID或使用 'roadmap switch <roadmap_id>' 设置活动路线图。[/red]")
            return 1

        # 根据类型显示不同内容
        if type == "milestone":
            # 显示路线图的所有里程碑
            result = handle_show_all_milestones(
                service=service,
                roadmap_id=roadmap_id,
                format="yaml",  # 使用YAML格式
            )
        elif type == "epic" or type == "story":
            # 显示路线图的所有史诗或故事
            result = handle_show_elements_by_type(
                service=service,
                roadmap_id=roadmap_id,
                element_type=type,
                format="yaml",  # 使用YAML格式
            )
        else:
            # 默认显示路线图详情
            result = handle_show_roadmap(
                service=service,
                roadmap_id=roadmap_id,
                milestone_id=None,
                task_id=None,
                health=False,
                format="yaml",  # 使用YAML格式
            )

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '获取详情失败')}[/red]")
            return 1

        # 直接打印输出内容，不使用Rich控制台
        print(result["data"]["formatted_output"])
        return 0

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="export", help="导出路线图为YAML")
@click.option("--id", "-i", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--output", "-o", required=True, type=click.Path(), help="输出文件路径(必填)")
@pass_service
def export(
    service,
    id: Optional[str],
    output: str,
):
    """导出路线图为YAML文件"""
    # 直接导入处理器函数
    from .handlers.operations_handlers import export_to_yaml

    try:
        # 直接调用处理器函数
        result = export_to_yaml(service, id, output)

        if result.get("success"):
            console.print(f"[green]✓ 路线图已导出到: {result['file_path']}[/green]")
        else:
            console.print(f"[red]✗ 导出失败: {result['error']}[/red]")
            return 1

        return 0
    except Exception as e:
        console.print(f"[red]执行导出时发生错误: {e}[/red]")
        return 1


@roadmap.command(name="delete", help="删除路线图或元素")
@click.argument("type", type=click.Choice(["roadmap", "milestone", "epic", "story"]))
@click.argument("id")
@click.option("--force", "-f", is_flag=True, help="强制删除，不请求确认")
@click.option("--cascade", "-c", is_flag=True, help="级联删除关联元素")
@pass_service
def delete(service, type: str, id: str, force: bool, cascade: bool):
    """删除路线图或元素"""
    try:
        # 获取对象信息
        name = get_object_name(service, type, id)

        # 确认删除
        if not force:
            if not click.confirm(f"确定要删除{get_type_name(type)} '{name}' ({id})吗?"):
                console.print("[yellow]操作已取消[/yellow]")
                return 1

        # 执行删除
        result = handle_delete(service, type, id, cascade)

        # 处理结果
        if result.get("success"):
            message = f"{get_type_name(type)} '{name}' ({id}) 已成功删除"
            console.print(f"[green]{message}[/green]")
            return 0
        else:
            error_message = f"删除失败: {result.get('error', '未知错误')}"
            console.print(f"[red]{error_message}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]删除过程中出错: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(roadmap())
