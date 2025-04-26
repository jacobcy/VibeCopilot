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
from src.cli.commands.roadmap.handlers.list_handlers import handle_list_elements, handle_list_roadmaps
from src.cli.commands.roadmap.handlers.plan_handlers import handle_plan_roadmap
from src.cli.commands.roadmap.handlers.show_handlers import handle_show_roadmap
from src.cli.commands.roadmap.handlers.story_handlers import handle_story_command
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
@click.option("--theme", help="GitHub项目主题标签")
@click.option(
    "--operation",
    type=click.Choice(["push", "pull"]),
    default="pull",
    help="同步操作类型",
)
@click.option("--roadmap", help="指定路线图ID")
@click.option("--force", is_flag=True, help="强制同步，忽略冲突")
@click.option("--verbose", is_flag=True, help="显示详细输出")
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


@roadmap.command(name="list", help="列出路线图元素或所有路线图")
@click.option("--all", is_flag=True, help="列出所有路线图而非当前路线图中的元素")
@click.option(
    "--type",
    type=click.Choice(["all", "milestone", "story", "task"]),
    default="all",
    help="元素类型",
)
@click.option("--status", help="按状态筛选")
@click.option("--assignee", help="按负责人筛选")
@click.option("--labels", help="按标签筛选，多个标签用逗号分隔")
@click.option("--detail", is_flag=True, help="显示详细信息")
@click.option(
    "--format",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="输出格式",
)
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.argument("extra_args", nargs=-1)  # 捕获所有可能的额外参数
@pass_service
def list_roadmaps(
    service,
    all=False,
    type="all",
    status=None,
    assignee=None,
    labels=None,
    detail=False,
    format="text",
    verbose=False,
    extra_args=None,
):
    """列出路线图元素或所有路线图"""
    # 检查是否有额外的非选项参数
    if extra_args:
        # 有错误的位置参数
        console.print("[bold red]命令格式错误[/bold red]")
        console.print(f"[red]无法识别的参数: {' '.join(extra_args)}[/red]")
        console.print("\n[yellow]提示:[/yellow] roadmap list 命令参数需要使用 '--' 前缀，例如:")
        console.print("  vibecopilot roadmap list --all")
        console.print("  vibecopilot roadmap list --type milestone --status active --format table")
        console.print("\n[blue]查看帮助:[/blue] vibecopilot roadmap list --help")
        return 1

    try:
        if all:
            # 列出所有路线图
            result = handle_list_roadmaps(service=service, detail=detail, format=format, verbose=verbose)
        else:
            # 列出路线图元素
            result = handle_list_elements(
                service=service,
                type=type,
                status=status,
                assignee=assignee,
                labels=labels,
                detail=detail,
                format=format,
                verbose=verbose,
            )

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '获取列表失败')}[/red]")
            return 1

        # 输出结果
        print(result.get("formatted_output", ""))

        # 如果是详细模式且有数据，显示额外信息
        if verbose and result.get("total"):
            print(f"\n共 {result.get('total')} 条记录")

        return 0

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="create", help="创建新的路线图元素或从文件生成标准YAML")
@click.argument("type", type=click.Choice(["milestone", "epic", "story"]), required=False)
@click.argument("title", required=False)
@click.option(
    "--source",
    type=click.Path(exists=True, dir_okay=False),
    help="用于生成路线图YAML的源文件 (Markdown或YAML)",
)
@click.option("--epic", help="所属史诗ID (用于story, 手动创建时)")
@click.option("--desc", help="详细描述 (手动创建时)")
@click.option("--assignee", help="指派给用户 (手动创建时)")
@click.option("--labels", help="标签列表，用逗号分隔 (手动创建时)")
@click.option(
    "--priority",
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
@click.argument("type", type=click.Choice(["milestone", "story", "task"]))
@click.argument("id")
@click.argument("status")
@click.option("--sync", is_flag=True, help="同步到GitHub")
@click.option("--comment", help="更新说明")
@click.option("--assignee", help="更新指派人")
@click.option("--labels", help="更新标签（用逗号分隔）")
@pass_service
def update(
    service,
    type: str,
    id: str,
    status: str,
    sync: bool = False,
    comment: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
):
    """更新路线图元素状态"""
    from .handlers.update_handlers import RoadmapUpdateHandlers

    update_args = {
        "type": type,
        "id": id,
        "status": status,
        "sync": sync,
        "comment": comment,
        "assignee": assignee,
        "labels": labels,
    }

    try:
        result = RoadmapUpdateHandlers.handle_update_command(update_args, service)

        if result.get("status") == "success":
            console.print(f"[green]✓ {result.get('message')}[/green]")
            return 0
        elif result.get("status") == "warning":
            console.print(f"[yellow]⚠ {result.get('message')}[/yellow]")
            if "sync_error" in result.get("data", {}):
                console.print(f"[yellow]GitHub同步错误: {result['data']['sync_error']}[/yellow]")
            return 0
        else:
            console.print(f"[red]✗ {result.get('message', '更新失败')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="story", help="管理路线图故事")
@click.argument("story_id", required=False)
@click.option("--title", help="故事标题")
@click.option("--milestone", help="所属里程碑ID")
@click.option("--desc", help="故事描述")
@click.option("--priority", type=click.Choice(["P0", "P1", "P2", "P3"]), help="优先级")
@click.option("--assignee", help="指派给用户")
@click.option("--labels", help="标签列表，用逗号分隔")
@click.option(
    "--status",
    type=click.Choice(["not_started", "in_progress", "completed", "blocked"]),
    help="更新状态",
)
@click.option("--comment", help="状态变更说明")
@click.option(
    "--format",
    type=click.Choice(["json", "text", "table"]),
    default="text",
    help="输出格式",
)
@click.option("--delete", is_flag=True, help="删除故事")
@click.option("--force", is_flag=True, help="强制删除，不请求确认")
@pass_service
def story(
    service,
    story_id=None,
    title=None,
    milestone=None,
    description=None,
    priority=None,
    assignee=None,
    labels=None,
    status=None,
    comment=None,
    format="text",
    delete=False,
    force=False,
):
    """管理路线图故事"""
    try:
        result = handle_story_command(
            service=service,
            story_id=story_id,
            title=title,
            milestone=milestone,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=labels,
            status=status,
            comment=comment,
            format=format,
            delete=delete,
            force=force,
        )

        if result.get("success"):
            if "formatted_output" in result.get("data", {}):
                print(result["data"]["formatted_output"])
            else:
                console.print(f"[green]{result.get('message')}[/green]")
            return 0
        else:
            console.print(f"[red]{result.get('message')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        return 1


@roadmap.command(name="validate", help="验证路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="修复后输出的文件路径")
@click.option("--template", type=click.Path(exists=True), help="使用自定义模板验证")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--import", "import_data", is_flag=True, help="验证通过后导入路线图")
@click.option("--roadmap-id", help="导入时指定路线图ID")
@pass_service
@async_command
async def validate(
    service,
    source: str,
    output: Optional[str] = None,
    template: Optional[str] = None,
    verbose: bool = False,
    import_data: bool = False,
    roadmap_id: Optional[str] = None,
):
    """验证路线图YAML文件格式"""
    from .handlers.validate_handlers import RoadmapValidateHandlers

    try:
        validate_args = {
            "source": source,
            "output": output,
            "template": template,
            "verbose": verbose,
            "import_data": import_data,
            "roadmap_id": roadmap_id,
        }

        result = await RoadmapValidateHandlers.handle_validate_command(validate_args, service)

        # 显示验证结果
        if result.get("success") and not result.get("warnings") and not result.get("errors"):
            console.print("[bold green]✅ 验证通过，文件格式完全符合要求[/bold green]")
            return 0

        # 显示警告
        if result.get("warnings"):
            console.print("\n[bold yellow]警告:[/bold yellow]")
            for warning in result["warnings"]:
                console.print(f"[yellow]⚠️ {warning}[/yellow]")

        # 显示错误
        if result.get("errors"):
            console.print("\n[bold red]错误:[/bold red]")
            for error in result["errors"]:
                console.print(f"[red]❌ {error}[/red]")

        # 显示修复结果
        if result.get("fixed"):
            console.print(f"\n[green]{result.get('message')}[/green]")

        # 显示导入结果
        if result.get("imported"):
            console.print(f"\n[green]{result.get('message')}[/green]")

        # 返回状态码
        return 0 if result.get("success") else 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        if verbose:
            console.print("[red]详细错误信息:[/red]")
            import traceback

            console.print(traceback.format_exc())
        return 1


@roadmap.command(name="import", help="导入路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--roadmap-id", help="现有路线图ID，不提供则创建新路线图")
@click.option("--fix", is_flag=True, help="自动修复格式问题")
@click.option("--activate", is_flag=True, help="导入后设为当前活动路线图")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service
@async_command
async def import_roadmap(
    service,
    source: str,
    roadmap_id: Optional[str],
    fix: bool,
    activate: bool,
    verbose: bool,
):
    """从YAML文件导入路线图"""
    try:
        # 调用导入处理器
        result = await handle_import(source, service, roadmap_id, fix, activate, verbose)

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
@click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--milestone", help="里程碑ID")
@click.option("--task", help="任务ID")
@click.option("--health", is_flag=True, help="显示健康状态检查")
@click.option(
    "--format",
    type=click.Choice(["json", "text", "table"]),
    default="table",
    help="输出格式",
)
@pass_service
def show(service, id=None, milestone=None, task=None, health=False, format="table"):
    """查看路线图详情"""
    try:
        result = handle_show_roadmap(
            service=service,
            roadmap_id=id,
            milestone_id=milestone,
            task_id=task,
            health=health,
            format=format,
        )

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '获取详情失败')}[/red]")
            return 1

        print(result["data"]["formatted_output"])
        return 0

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="export", help="导出路线图为YAML")
@click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--output", required=True, type=click.Path(), help="输出文件路径(必填)")
@click.option("--milestone", help="只导出特定里程碑及其任务")
@click.option("--template", type=click.Path(exists=True), help="使用特定模板格式")
@pass_service
def export(
    service,
    id: Optional[str],
    output: str,
    milestone: Optional[str] = None,
    template: Optional[str] = None,
):
    """导出路线图为YAML文件"""
    # 直接导入处理器函数
    from .handlers.operations_handlers import export_to_yaml

    try:
        # 直接调用处理器函数
        # 注意：当前实现只使用id和output参数，milestone和template参数未使用
        # TODO: 实现milestone和template参数的支持
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
@click.argument("type", type=click.Choice(["roadmap", "milestone", "task"]))
@click.argument("id")
@click.option("--force", is_flag=True, help="强制删除，不请求确认")
@click.option("--cascade", is_flag=True, help="级联删除关联元素")
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


@roadmap.command(name="plan", help="互动式路线图规划")
@click.option("--id", help="要修改的路线图ID")
@click.option("--template", help="使用特定模板开始")
@click.option("--from", "from_file", type=click.Path(exists=True), help="从YAML文件开始")
@click.option("--interactive", is_flag=True, help="始终使用交互式模式")
@pass_service
def plan(service, id=None, template=None, from_file=None, interactive=False):
    """互动式路线图规划"""
    try:
        result = handle_plan_roadmap(
            service=service,
            roadmap_id=id,
            template=template,
            from_file=from_file,
            interactive=interactive,
        )

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '规划失败')}[/red]")
            return 1

        roadmap_id = result.get("roadmap_id")
        console.print(f"[green]{result.get('message', '规划完成')}[/green]")

        if result.get("roadmap", {}).get("is_active"):
            console.print(f"[green]已设置 {roadmap_id} 为活动路线图[/green]")

        return 0

    except Exception as e:
        console.print(f"[bold red]执行错误:[/bold red] {str(e)}")
        return 1


@roadmap.command(name="status", help="显示路线图状态")
@click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--detail", is_flag=True, help="显示详细统计信息")
@pass_service
def status(service, id=None, detail=False):
    """显示路线图状态，包括基本信息或详细统计信息。"""
    try:
        roadmap_id = id or service.active_roadmap_id
        if not roadmap_id:
            console.print("[red]错误: 未指定路线图ID，且未设置活动路线图。[/red]")
            return 1

        result = None
        output_data = None
        output_title = ""

        if detail:
            # --- detail 分支：调用服务层，简化输出 ---
            result = service.get_roadmap_info(roadmap_id)
            output_title = f"路线图详细信息 ({roadmap_id})"
            if result and result.get("success"):
                # 准备用于简单输出的数据
                output_data = {
                    "roadmap": result.get("roadmap", {}),
                    "stats": result.get("stats", {}),
                    # "status": result.get("status", {}) # get_roadmap_info 返回的 status 不一定有意义了
                }
        else:
            # --- 默认分支：调用服务层获取基本信息，简化输出 ---
            roadmap_data = service.get_roadmap(roadmap_id)
            is_active = roadmap_id == service.active_roadmap_id
            if roadmap_data:
                result = {"success": True}
                output_title = f"路线图基本状态 ({roadmap_id})"
                # 准备用于简单输出的数据
                output_data = {
                    "id": roadmap_id,
                    "name": roadmap_data.get("title", roadmap_data.get("name", "N/A")),
                    "description": roadmap_data.get("description", ""),
                    "version": roadmap_data.get("version", "N/A"),
                    "is_active": is_active,
                }
            else:
                result = {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # --- 统一处理结果和输出 ---
        if result and result.get("success") and output_data:
            console.print(f"[bold cyan]{output_title}[/bold cyan]")
            # 使用 YAML 格式简单打印准备好的数据
            import yaml
            from rich.syntax import Syntax

            try:
                yaml_string = yaml.safe_dump(output_data, allow_unicode=True, sort_keys=False, indent=2)
                syntax = Syntax(yaml_string, "yaml", theme="default", line_numbers=False)
                console.print(syntax)
            except yaml.YAMLError as e:
                logger.error(f"转换为 YAML 输出失败: {e}")
                console.print(output_data)  # YAML 失败则打印原始字典
            return 0
        elif result:
            console.print(f"[red]获取状态失败: {result.get('error', '未知错误')}[/red]")
            return 1
        else:
            # 如果 result 是 None (理论上不应该发生)
            console.print("[red]获取状态时发生未知错误。[/red]")
            return 1

    except Exception as e:
        logger.error(f"获取路线图状态时出错: {e}", exc_info=True)
        console.print(f"[red]获取路线图状态时出错: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(roadmap())
