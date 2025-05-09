"""
路线图管理命令模块

处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import asyncio
import logging
import sys
from functools import wraps
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.prompt import Confirm

from src.cli.commands.roadmap.handlers.delete_handlers import get_object_name, get_type_name, handle_delete
from src.cli.commands.roadmap.handlers.import_handlers import handle_import
from src.cli.commands.roadmap.handlers.list_handlers import handle_list_roadmaps
from src.cli.commands.roadmap.handlers.operations_handlers import export_to_yaml, handle_link_github, handle_validate
from src.cli.commands.roadmap.handlers.show_handlers import handle_show_all_milestones, handle_show_elements_by_type, handle_show_roadmap
from src.cli.commands.roadmap.handlers.switch_handlers import handle_switch_roadmap
from src.cli.commands.roadmap.handlers.sync_handlers import handle_sync_roadmap
from src.cli.commands.roadmap.handlers.update_handlers import RoadmapUpdateHandlers
from src.core.config import get_config

# Import the RoadmapServiceFacade
from src.roadmap.service import RoadmapService  # 用于向后兼容
from src.roadmap.service.roadmap_service_facade import RoadmapServiceFacade
from src.status.service import StatusService
from src.sync.github_project import GitHubProjectSync

# 保留以便在命令行处理中使用
from src.utils import console_utils
from src.utils.console_utils import print_error, print_info, print_success, print_warning

# 从main.py导入CLIContext (假设已将其移至模块顶部)
try:
    from src.cli.main import CLIContext
except ImportError:
    # 如果CLIContext仍在main函数内部，这里可能需要调整或采用其他方式获取服务
    # 但最好是将CLIContext移到模块级别
    CLIContext = object  # 占位符，表示无法直接导入

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


@roadmap.command(name="sync", help="将本地路线图与关联的 GitHub 项目同步")
@click.argument("operation", type=click.Choice(["push", "pull"]))
@click.argument("id", required=False)  # 本地ID或远程标识符(Number或Node ID)
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
@click.option("--force", "-f", is_flag=True, help="Force sync operation")
@click.pass_obj
@async_command
async def sync(service, operation: str, id: Optional[str], verbose: bool, force: bool):
    """将本地路线图与关联的 GitHub 项目同步。

    OPERATION: 同步操作类型 (push: 本地 -> GitHub, pull: GitHub -> 本地)
    ID: push操作时为本地路线图ID，pull操作时为远程项目编号(Number)或Node ID
    """
    try:
        # 调用同步处理器函数
        result = await handle_sync_roadmap(service, operation, id, force, verbose)

        if result.get("status") == "success":
            console_utils.print_success(result.get("message", "同步操作成功"))
            if verbose and result.get("details"):
                console.print(f"[bold]同步详情:[/]\n{result.get('details')}")
            return 0
        else:
            console_utils.print_error(result.get("message", "同步操作失败"))
            return 1

    except Exception as e:
        console.print(f"[red]✗ 同步命令执行失败: {str(e)}[/red]")
        logger.error(f"同步命令执行失败: {e}", exc_info=True)
        return 1


@roadmap.command(name="switch", help="切换活动路线图")
@click.argument("roadmap_id", required=False)
@click.option("--show", is_flag=True, help="只显示当前活动路线图")
@click.option("--clear", is_flag=True, help="清除当前活动路线图设置")
@click.pass_obj
def switch(cli_context, roadmap_id=None, show=False, clear=False):
    """切换活动路线图

    ROADMAP_ID: 路线图ID，不提供则显示当前活动路线图
    """
    try:
        # 原来的错误调用:
        # result = handle_switch_roadmap(service, roadmap_id, show, clear)

        # 正确的方式: 实例化 RoadmapService 并传递
        from src.roadmap.service import RoadmapService  # 确保导入

        roadmap_service_instance = RoadmapService()  # 创建 RoadmapService 实例
        result = handle_switch_roadmap(roadmap_service_instance, roadmap_id, show, clear)  # 使用正确的实例

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
@click.option("--remote", "-r", is_flag=True, help="列出远程GitHub Project作为路线图")
@click.pass_obj
def list_roadmaps(
    cli_context,
    remote: bool,
):
    """列出所有路线图"""
    console.print("[bold cyan]=== 路线图列表 ===[/bold cyan]")

    if remote:
        console.print("\n正在获取远程GitHub Projects...")
        github_sync = GitHubProjectSync()
        projects_result = github_sync.get_github_projects()

        if projects_result.get("success"):
            projects = projects_result.get("projects", [])
            if projects:
                console.print(f"找到 {len(projects)} 个远程GitHub Projects:")
                # 确保项目字典包含预期的键
                for project in projects:
                    number = project.get("number", "N/A")
                    title = project.get("title", "未知标题")
                    state = project.get("state", "未知状态")
                    project_id = project.get("id", "N/A")  # 这里的id是node id
                    console.print(f"  [bold]- {title}[/bold] (Number: {number}, ID: {project_id}, 状态: {state})")
            else:
                console_utils.print_info("未找到远程GitHub Projects。")
        else:
            error_message = projects_result.get("message", "获取远程GitHub Projects 失败。")
            console_utils.print_error(f"错误: {error_message}")
    else:
        # --- 修正调用本地路线图处理函数 ---
        # 原来的错误调用:
        # handle_list_roadmaps(service)

        # 正确的方式: 实例化 RoadmapService 并传递
        from src.roadmap.service import RoadmapService  # 确保导入

        roadmap_service_instance = RoadmapService()  # 创建 RoadmapService 实例
        result = handle_list_roadmaps(roadmap_service_instance)  # 使用正确的实例

        # 处理 handle_list_roadmaps 的返回结果并打印
        if result.get("success"):
            if result.get("formatted_output"):
                # rich_console.print 会自动处理换行符，所以直接打印
                console.print(result["formatted_output"], end="")  # end="" 避免额外换行
            elif result.get("message"):  # 如果没有 formatted_output 但有消息
                # 根据消息类型选择打印方式
                if "没有找到任何路线图" in result["message"]:
                    console_utils.print_info(result["message"])
                else:
                    console.print(result["message"])
        else:
            console_utils.print_error(result.get("message", "列出路线图失败"))


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
@click.pass_obj
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
@click.pass_obj
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
@click.pass_obj
def validate(
    service,
    source: str,
    verbose: bool = False,
):
    """验证路线图YAML文件格式"""
    try:
        # 使用处理器函数进行验证
        result = handle_validate(source, verbose)

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

        # 根据验证结果返回适当的状态码
        return 0 if result.get("success") else 1

    except Exception as e:
        console.print(f"[red]执行出错: {str(e)}[/red]")
        if verbose and result.get("error_details"):
            console.print("[red]详细错误信息:[/red]")
            console.print(result["error_details"])
        return 1


@roadmap.command(name="import", help="导入路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--activate", "-a", is_flag=True, help="导入后设为当前活动路线图")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.pass_obj
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


@roadmap.command(name="show", help="查看路线图或其元素的详情")
@click.argument("identifier", required=False, default=None)
@click.option(
    "--type",
    "-t",
    "type_option",
    type=click.Choice(["roadmap", "milestone", "epic", "story"]),
    default=None,
    help="要显示的元素类型。如果省略，会尝试从 IDENTIFIER 推断，或默认为 roadmap。",
)
@click.pass_obj
def show(cli_context, identifier: Optional[str], type_option: Optional[str]):
    """
    查看路线图或其元素的详情。

    IDENTIFIER: 路线图/元素的ID (如 rm_xxxx) 或名称。
                如果省略，且类型为 roadmap (或省略类型)，则显示当前活动路线图。
                如果省略，且类型为 milestone/epic/story，则列出活动路线图下的所有此类元素。
    """
    from .handlers.show_handlers import handle_show_command

    try:
        # Instantiate RoadmapService correctly
        from src.roadmap.service import RoadmapService  # Ensure import

        roadmap_service_instance = RoadmapService()  # Create RoadmapService instance

        # Pass the RoadmapService instance
        result = handle_show_command(roadmap_service_instance, identifier, type_option)

        if not result.get("success"):
            console.print(f"[red]{result.get('message', '获取详情失败')}[/red]")
            return 1

        # Use console.print for rich output
        if result.get("data") and result["data"].get("formatted_output"):
            console.print(result["data"]["formatted_output"], end="")  # end="" if formatted_output handles newlines
        elif result.get("message"):  # Fallback if no formatted_output but there's a message
            console.print(result.get("message"))
        return 0

    except Exception as e:
        console.print(f"[bold red]执行show命令时出错: {str(e)}[/bold red]")
        logger.error(f"Error in roadmap show command: {e}", exc_info=True)
        return 1


@roadmap.command(name="export", help="导出路线图为YAML")
@click.option("--id", "-i", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--output", "-o", required=True, type=click.Path(), help="输出文件路径(必填)")
@click.pass_obj
def export(
    service,
    id: Optional[str],
    output: str,
):
    """导出路线图为YAML文件"""
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
@click.argument("identifier", required=True)
@click.option("--force", "-f", is_flag=True, help="强制删除，不请求确认")
@click.pass_obj
def delete(service_obj, identifier: str, force: bool):
    """删除路线图或元素"""
    try:
        # 从 ID 推断实体类型
        from src.utils.id_generator import EntityType, IdGenerator

        entity_type_enum = IdGenerator.get_entity_type_from_id(identifier)
        if not entity_type_enum:
            console.print(f"[red]无效的ID: {identifier}[/red]")
            return 1
        type_mapping = {
            EntityType.ROADMAP: "roadmap",
            EntityType.MILESTONE: "milestone",
            EntityType.STORY: "story",
            EntityType.EPIC: "epic",
            EntityType.TASK: "task",
        }
        type_arg = type_mapping.get(entity_type_enum)
        if not type_arg:
            console.print(f"[red]不支持的实体类型: {entity_type_enum.name}[/red]")
            return 1
        id_arg = identifier

        # 实例化 RoadmapService
        from src.roadmap.service import RoadmapService

        service = RoadmapService()

        # 获取对象名称
        name = get_object_name(service, type_arg, id_arg)

        # 确认删除
        if not force:
            if not click.confirm(f"确定要删除{get_type_name(type_arg)} '{name}' ({id_arg})吗? "):
                console.print("[yellow]操作已取消[/yellow]")
                return 1

        # 执行删除，总是级联删除
        result = handle_delete(service, type_arg, id_arg)

        # 处理结果
        if result.get("success"):
            console.print(f"[green]{get_type_name(type_arg)} '{name}' ({id_arg}) 已成功删除[/green]")
            return 0
        else:
            console.print(f"[red]删除失败: {result.get('message', '未知错误')}[/red]")
            return 1

    except Exception as e:
        console.print(f"[red]删除过程中出错: {str(e)}[/red]")
        return 1


@roadmap.command(name="link", help="关联本地路线图到 GitHub 项目或显示现有链接")
@click.option("--project-identifier", "-p", required=False, help="GitHub项目编号 (UI Number) 或 Node ID (创建链接时必需)")
@click.option("--roadmap-id", "-i", help="要关联的本地路线图ID (默认为当前活动路线图)")
@click.option("--list", "-l", "list_links", is_flag=True, help="显示当前已建立的本地路线图与GitHub Project的链接")
@click.pass_obj
@async_command
async def link_github(ctx_obj, project_identifier: Optional[str], roadmap_id: Optional[str], list_links: bool):
    """关联本地路线图到 GitHub 项目或显示现有链接。

    Owner 和 Repo 信息将从全局配置中自动获取。
    如果配置缺失，请运行 'vc status init'。
    """
    # 检查参数组合
    if list_links:
        if project_identifier or roadmap_id:
            console_utils.print_warning("使用 --list 时，将忽略 --project-identifier 和 --roadmap-id 参数。")
        # 调用处理函数显示列表
        result = handle_link_github(list_links=True, ctx_obj=ctx_obj)
    elif project_identifier:
        # 创建链接操作，现在不需要 owner 和 repo 作为参数
        result = handle_link_github(
            project_identifier=project_identifier,
            local_roadmap_id=roadmap_id,
            list_links=False,
            ctx_obj=ctx_obj
            # owner 和 repo 将在 handler 内部获取
        )
    else:
        # 参数不足以执行操作 (既不是 list 也不是 create)
        console_utils.print_error("请提供 --project-identifier 来创建链接，或使用 --list 查看现有链接。")
        return 1  # Indicate error

    # 处理结果
    if result.get("success"):
        console_utils.print_success(result.get("message", "操作成功"))
        # 如果是列表操作且有内容，打印链接
        if list_links and result.get("links"):
            if result["links"]:
                console.print("[bold]现有链接:[/]")
                for local_id, gh_id in result["links"].items():
                    console.print(f"  - 本地路线图: {local_id} <-> GitHub Project: {gh_id}")
            else:
                console_utils.print_info("当前没有已建立的链接。")
        return 0
    else:
        console_utils.print_error(result.get("message", "操作失败"))
        return 1


if __name__ == "__main__":
    import asyncio

    asyncio.run(roadmap())
