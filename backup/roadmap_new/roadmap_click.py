"""
路线图管理命令模块 (Click实现)

使用Click框架处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import click
from click.exceptions import BadParameter, MissingParameter, UsageError
from rich.console import Console

from src.cli.decorators import pass_service
from src.roadmap import RoadmapService

console = Console()


# 创建一个友好的错误处理装饰器
def friendly_error_handling(func):
    """装饰器: 友好处理命令行参数错误"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (UsageError, BadParameter, MissingParameter) as e:
            # 获取原始错误消息
            error_msg = str(e)

            # 检查是否是参数错误
            if "Got unexpected extra arguments" in error_msg:
                incorrect_args = error_msg.split("Got unexpected extra arguments")[-1].strip("() ")
                console.print("[bold red]命令格式错误[/bold red]")
                console.print(f"[red]无法识别的参数: {incorrect_args}[/red]")

                # 为roadmap list命令提供特定帮助
                if "list" in func.__name__:
                    console.print("\n[yellow]提示:[/yellow] roadmap list 命令参数需要使用 '--' 前缀，例如:")
                    console.print("  roadmap list --all")
                    console.print("  roadmap list --type=milestone --status=active")
                    console.print("\n正确用法示例:")
                    console.print("  roadmap list --type milestone --status active --format table")
                    console.print("  roadmap list --all --detail")
                else:
                    console.print("\n[yellow]提示:[/yellow] 命令参数可能需要使用 '--' 前缀，请查看帮助")

                console.print(f"\n[blue]查看详细帮助请使用:[/blue] roadmap {func.__name__.replace('_roadmaps', '')} --help")
            else:
                # 其他类型的错误
                console.print(f"[bold red]命令错误:[/bold red] {error_msg}")
                console.print("[yellow]提示:[/yellow] 请检查命令格式是否正确")

            return 1

    return wrapper


@click.group(help="路线图管理命令")
def roadmap():
    """路线图管理命令组"""
    pass


@roadmap.command(name="sync", help="从GitHub同步路线图数据")
@click.argument("repository", required=True)
@click.option("--theme", help="GitHub项目主题标签")
@click.option("--branch", default="main", help="要同步的分支名称")
@click.option("--verbose", is_flag=True, help="显示详细输出")
@pass_service
def sync(service, repository, theme=None, branch="main", verbose=False):
    """从GitHub同步路线图数据

    REPOSITORY: GitHub仓库名称，格式：所有者/仓库名
    """
    from src.cli.commands.roadmap_new.handlers.sync_handler import handle_sync_command

    sync_args = {"repository": repository, "theme": theme, "branch": branch, "verbose": verbose, "_agent_mode": False}

    try:
        result = handle_sync_command(sync_args, service)

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
    if show:
        # 显示当前活动路线图
        active_id = service.active_roadmap_id
        if active_id:
            roadmap = service.get_roadmap(active_id)
            if roadmap:
                roadmap_name = roadmap.get("name") or roadmap.get("title") or "[未命名路线图]"
                console.print(f"当前活动路线图: [bold]{roadmap_name}[/bold] (ID: {active_id})")
            else:
                console.print(f"当前活动路线图ID: {active_id}，但无法获取详细信息")
        else:
            console.print("[yellow]当前未设置活动路线图[/yellow]")
        return 0

    if clear:
        # 清除当前活动路线图
        service._active_roadmap_id = None
        console.print("[green]已清除活动路线图设置[/green]")
        return 0

    if not roadmap_id:
        # 如果既没有指定--show也没有提供roadmap_id，显示当前活动路线图
        active_id = service.active_roadmap_id
        if active_id:
            roadmap = service.get_roadmap(active_id)
            if roadmap:
                roadmap_name = roadmap.get("name") or roadmap.get("title") or "[未命名路线图]"
                console.print(f"当前活动路线图: [bold]{roadmap_name}[/bold] (ID: {active_id})")
            else:
                console.print(f"当前活动路线图ID: {active_id}，但无法获取详细信息")
        else:
            console.print("[yellow]当前未设置活动路线图[/yellow]")
            console.print("请使用 'roadmap switch <roadmap_id>' 设置活动路线图，或使用 'roadmap list --all' 查看所有可用路线图")
        return 0

    # 执行切换
    result = service.switch_roadmap(roadmap_id)

    if result.get("success", False):
        roadmap_name = result.get("roadmap_name") or "[未命名路线图]"
        console.print(f"[green]✓ 已切换到路线图: {roadmap_name} (ID: {result.get('roadmap_id')})[/green]")
        return 0
    else:
        console.print(f"[red]✗ 切换失败: {result.get('error', '未知错误')}[/red]")
        return 1


@roadmap.command(name="list", help="列出路线图元素或所有路线图")
@click.option("--all", is_flag=True, help="列出所有路线图而非当前路线图中的元素")
@click.option("--type", type=click.Choice(["all", "milestone", "story", "task"]), default="all", help="元素类型")
@click.option("--status", help="按状态筛选")
@click.option("--assignee", help="按负责人筛选")
@click.option("--labels", help="按标签筛选，多个标签用逗号分隔")
@click.option("--detail", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json", "table"]), default="text", help="输出格式")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service
@friendly_error_handling
def list_roadmaps(service, all=False, type="all", status=None, assignee=None, labels=None, detail=False, format="text", verbose=False):
    """列出路线图元素或所有路线图"""
    from src.cli.commands.roadmap_new.handlers.list_handler import handle_list_command

    # 创建参数字典
    args = {
        "all": all,
        "type": type,
        "status": status,
        "assignee": assignee,
        "labels": labels,
        "detail": detail,
        "format": format,
        "verbose": verbose,
    }

    # 调用处理函数
    result = handle_list_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(result.get("formatted_output", ""))
        return 0
    else:
        console.print(f"[red]错误: {result.get('message', '未知错误')}[/red]")
        return 1


@roadmap.command(name="show", help="查看路线图详情")
@click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--milestone", help="里程碑ID")
@click.option("--task", help="任务ID")
@click.option("--health", is_flag=True, help="显示健康状态检查")
@click.option("--format", type=click.Choice(["json", "text", "table"]), default="table", help="输出格式")
@pass_service
def show(service, id=None, milestone=None, task=None, health=False, format="table"):
    """查看路线图详情"""
    from src.cli.commands.roadmap_new.handlers.show_handler import handle_show_command

    # 创建参数字典
    args = {"id": id, "milestone": milestone, "task": task, "health": health, "format": format}

    # 调用处理函数
    result = handle_show_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(result.get("formatted_output", ""))
        return 0
    else:
        console.print(f"[red]错误: {result.get('message', '未知错误')}[/red]")
        return 1


@roadmap.command(name="create", help="创建新的路线图")
@click.argument("name")
@click.option("--description", help="路线图描述")
@pass_service
def create(service, name, description=None):
    """创建新的路线图"""
    from src.cli.commands.roadmap_new.handlers.create_handler import handle_create_command

    # 创建参数字典
    args = {"name": name, "description": description}

    # 调用处理函数
    result = handle_create_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]✓ {result.get('message', '路线图创建成功')}[/green]")
        return 0
    else:
        console.print(f"[red]✗ 创建失败: {result.get('message', '未知错误')}[/red]")
        return 1


@roadmap.command(name="delete", help="删除路线图或元素")
@click.argument("id", required=True)
@click.option("--type", type=click.Choice(["roadmap", "milestone", "story", "task"]), help="要删除的元素类型")
@click.option("--force", is_flag=True, help="强制删除，不请求确认")
@click.option("--cascade", is_flag=True, help="级联删除关联元素")
@pass_service
def delete(service, id, type=None, force=False, cascade=False):
    """删除路线图或元素

    ID: 要删除的路线图或元素ID
    """
    from src.cli.commands.roadmap_new.handlers.delete_handler import handle_delete_command

    # 创建参数字典
    args = {"id": id, "type": type, "force": force, "cascade": cascade}

    # 调用处理函数
    result = handle_delete_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]✓ {result.get('message', '删除成功')}[/green]")
        return 0
    elif result.get("status") == "cancelled":
        console.print(f"[yellow]{result.get('message', '操作已取消')}[/yellow]")
        return 0
    else:
        console.print(f"[red]✗ {result.get('message', '删除失败')}[/red]")
        return 1


@roadmap.command(name="update", help="更新路线图元素状态")
@click.argument("id", required=True)
@click.option("--type", type=click.Choice(["roadmap", "milestone", "story", "task"]), help="要更新的元素类型")
@click.option("--status", help="更新状态")
@click.option("--name", help="更新名称")
@click.option("--description", help="更新描述")
@click.option("--priority", help="更新优先级")
@click.option("--assignee", help="更新负责人")
@click.option("--labels", help="更新标签，多个标签用逗号分隔")
@click.option("--start-date", help="更新开始日期")
@click.option("--end-date", help="更新结束日期")
@pass_service
def update(
    service, id, type=None, status=None, name=None, description=None, priority=None, assignee=None, labels=None, start_date=None, end_date=None
):
    """更新路线图或元素

    ID: 要更新的路线图或元素ID
    """
    from src.cli.commands.roadmap_new.handlers.update_handler import handle_update_command

    # 创建参数字典
    args = {
        "id": id,
        "type": type,
        "status": status,
        "name": name,
        "description": description,
        "priority": priority,
        "assignee": assignee,
        "labels": labels,
        "start_date": start_date,
        "end_date": end_date,
    }

    # 调用处理函数
    result = handle_update_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]✓ {result.get('message', '更新成功')}[/green]")
        return 0
    else:
        console.print(f"[red]✗ {result.get('message', '更新失败')}[/red]")
        return 1


@roadmap.command(name="export", help="导出路线图为YAML")
@click.option("--id", help="路线图ID，不提供则使用当前活动路线图")
@click.option("--output", required=True, type=click.Path(), help="输出文件路径")
@click.option("--milestone", help="只导出特定里程碑及其任务")
@click.option("--template", help="使用特定模板格式")
@pass_service
def export(service, id=None, output=None, milestone=None, template=None):
    """导出路线图为YAML文件"""
    from src.cli.commands.roadmap_new.handlers.export_handler import handle_export_command

    # 创建参数字典
    args = {"id": id, "output": output, "milestone": milestone, "template": template}

    # 调用处理函数
    result = handle_export_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]✓ {result.get('message', '路线图导出成功')}[/green]")
        return 0
    else:
        console.print(f"[red]✗ {result.get('message', '导出失败')}[/red]")
        return 1


@roadmap.command(name="import", help="导入路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--roadmap-id", help="现有路线图ID，不提供则创建新路线图")
@click.option("--fix", is_flag=True, help="自动修复格式问题")
@click.option("--activate", is_flag=True, help="导入后设为当前活动路线图")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service
def import_roadmap(service, source, roadmap_id=None, fix=False, activate=False, verbose=False):
    """从YAML文件导入路线图"""
    from src.cli.commands.roadmap_new.handlers.import_handler import handle_import_command

    # 创建参数字典
    args = {"source": source, "roadmap_id": roadmap_id, "fix": fix, "activate": activate, "verbose": verbose}

    # 调用处理函数
    result = handle_import_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        message = f"[green]✓ {result.get('message', '路线图导入成功')}[/green]"
        if result.get("data", {}).get("is_active"):
            message += "\n[green]此路线图已设置为当前活动路线图[/green]"
        console.print(message)
        return 0
    else:
        console.print(f"[red]✗ {result.get('message', '导入失败')}[/red]")
        return 1


@roadmap.command(name="validate", help="验证路线图YAML文件")
@click.argument("source", type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="自动修复格式问题")
@click.option("--output", type=click.Path(), help="修复后输出的文件路径")
@click.option("--template", type=click.Path(exists=True), help="使用自定义模板验证")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service
def validate(service, source, fix=False, output=None, template=None, verbose=False):
    """验证路线图YAML文件格式"""
    from src.cli.commands.roadmap_new.handlers.validate_handler import handle_validate_command

    # 创建参数字典
    args = {"source": source, "fix": fix, "output": output, "template": template, "verbose": verbose}

    # 调用处理函数
    result = handle_validate_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]✓ {result.get('message', 'YAML文件格式有效')}[/green]")
        return 0
    else:
        console.print(f"[red]✗ {result.get('message', '验证失败')}[/red]")
        return 1


@roadmap.command(name="story", help="查看路线图故事")
@click.argument("story_id", required=False)
@click.option("--milestone", help="里程碑ID")
@click.option("--status", help="筛选状态")
@click.option("--assignee", help="筛选指派人")
@click.option("--labels", help="筛选标签，多个标签用逗号分隔")
@click.option("--sort", help="排序字段 (id/title/status/priority/progress)")
@click.option("--desc", is_flag=True, help="降序排序")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service
def story(service, story_id=None, milestone=None, status=None, assignee=None, labels=None, sort="id", desc=False, format="table"):
    """查看路线图故事"""
    from src.cli.commands.roadmap_new.handlers.story_handler import handle_story_command

    # 创建参数字典
    args = {
        "story_id": story_id,
        "milestone": milestone,
        "status": status,
        "assignee": assignee,
        "labels": labels,
        "sort": sort,
        "desc": desc,
        "format": format,
    }

    # 调用处理函数
    result = handle_story_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(result.get("formatted_output", ""))
        return 0
    else:
        console.print(f"[red]错误: {result.get('message', '未知错误')}[/red]")
        return 1


@roadmap.command(name="plan", help="互动式路线图规划")
@click.option("--id", help="要修改的路线图ID")
@click.option("--template", help="使用特定模板开始")
@click.option("--from", "from_file", type=click.Path(exists=True), help="从YAML文件开始")
@click.option("--interactive", is_flag=True, help="始终使用交互式模式")
@pass_service
def plan(service, id=None, template=None, from_file=None, interactive=False):
    """互动式路线图规划"""
    from src.cli.commands.roadmap_new.handlers.plan_handler import handle_plan_command

    # 创建参数字典
    args = {"id": id, "template": template, "from_file": from_file, "interactive": interactive}

    # 调用处理函数
    result = handle_plan_command(args, service)

    # 输出结果
    if result.get("status") == "success":
        console.print(f"[green]{result.get('message', '路线图规划成功')}[/green]")
        return 0
    else:
        console.print(f"[red]错误: {result.get('message', '规划失败')}[/red]")
        return 1


if __name__ == "__main__":
    roadmap()
