# src/cli/commands/task/__init__.py

from typing import Any, Dict, List, Optional

import typer

from .task_comment_command import CommentTaskCommand
from .task_create_command import CreateTaskCommand
from .task_delete_command import DeleteTaskCommand
from .task_link_command import LinkTaskCommand, LinkType
from .task_list_command import ListTaskCommand
from .task_show_command import ShowTaskCommand
from .task_update_command import UpdateTaskCommand

# 其他子命令将在这里导入
# from .task_create_command import CreateTaskCommand
# ...

# 创建 Typer 应用 (子命令组)
task_app = typer.Typer(name="task", help="任务管理命令 (类似 GitHub issue)", no_args_is_help=True)  # 如果没有子命令，显示帮助

# 实例化并注册子命令
list_cmd_instance = ListTaskCommand()
show_cmd_instance = ShowTaskCommand()
create_cmd_instance = CreateTaskCommand()
update_cmd_instance = UpdateTaskCommand()
delete_cmd_instance = DeleteTaskCommand()
comment_cmd_instance = CommentTaskCommand()
link_cmd_instance = LinkTaskCommand()
# ...


# 使用 Typer 注册命令
# 注意：需要将命令实例的方法包装成 Typer 可调用的函数
# 或者直接在 Typer 回调中使用实例
@task_app.command(list_cmd_instance.name, help=list_cmd_instance.description)
def list_tasks(
    status: Optional[List[str]] = typer.Option(None, "--status", "-s", help="按状态过滤 (例如: open,in_progress)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="按负责人过滤"),
    label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="按标签过滤 (目前仅简单匹配)"),
    roadmap_item_id: Optional[str] = typer.Option(None, "--roadmap", "-r", help="按关联的 Roadmap Item (Story ID) 过滤"),
    independent: Optional[bool] = typer.Option(None, "--independent", "-i", help="仅显示独立任务 (无 Roadmap 关联)"),
    limit: Optional[int] = typer.Option(None, "--limit", help="限制返回数量"),
    offset: Optional[int] = typer.Option(None, "--offset", help="跳过指定数量的结果"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示更详细的信息"),
):
    """Typer 回调，调用 ListTaskCommand 的 execute 方法"""
    list_cmd_instance.execute(
        status=status,
        assignee=assignee,
        label=label,
        roadmap_item_id=roadmap_item_id,
        independent=independent,
        limit=limit,
        offset=offset,
        verbose=verbose,
    )


@task_app.command(show_cmd_instance.name, help=show_cmd_instance.description)
def show_task(
    task_id: str = typer.Argument(..., help="要显示的 Task ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示更详细的信息，包括评论"),
):
    """Typer 回调，调用 ShowTaskCommand 的 execute 方法"""
    show_cmd_instance.execute(task_id=task_id, verbose=verbose)


@task_app.command(create_cmd_instance.name, help=create_cmd_instance.description)
def create_task(
    title: str = typer.Option(..., "--title", "-t", help="任务标题 (必需)"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="任务描述"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="负责人"),
    label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="标签 (多个标签用多次选项)"),
    status: Optional[str] = typer.Option("open", "--status", "-s", help="初始状态 (默认: open)"),
    link_roadmap_item_id: Optional[str] = typer.Option(None, "--link-roadmap", help="关联到 Roadmap Item (Story ID)"),
    link_workflow_stage_instance_id: Optional[str] = typer.Option(None, "--link-workflow-stage", help="关联到 Workflow Stage Instance ID"),
    link_github_issue: Optional[str] = typer.Option(None, "--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)"),
):
    """Typer 回调，调用 CreateTaskCommand 的 execute 方法"""
    create_cmd_instance.execute(
        title=title,
        description=description,
        assignee=assignee,
        label=label,
        status=status,
        link_roadmap_item_id=link_roadmap_item_id,
        link_workflow_stage_instance_id=link_workflow_stage_instance_id,
        link_github_issue=link_github_issue,
    )


@task_app.command(update_cmd_instance.name, help=update_cmd_instance.description)
def update_task(
    task_id: str = typer.Argument(..., help="要更新的 Task ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="新的任务标题"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="新的任务描述"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="新的负责人 ('-' 表示清空)"),
    label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="设置新的标签列表 (覆盖旧列表)"),
    add_label: Optional[List[str]] = typer.Option(None, "--add-label", help="添加标签"),
    remove_label: Optional[List[str]] = typer.Option(None, "--remove-label", help="移除标签"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="新的状态"),
):
    """Typer 回调，调用 UpdateTaskCommand 的 execute 方法"""
    update_cmd_instance.execute(
        task_id=task_id,
        title=title,
        description=description,
        assignee=assignee,
        label=label,
        add_label=add_label,
        remove_label=remove_label,
        status=status,
    )


@task_app.command(delete_cmd_instance.name, help=delete_cmd_instance.description)
def delete_task(
    task_id: str = typer.Argument(..., help="要删除的 Task ID"),
    force: bool = typer.Option(False, "--force", "-f", help="跳过确认直接删除"),
):
    """Typer 回调，调用 DeleteTaskCommand 的 execute 方法"""
    delete_cmd_instance.execute(task_id=task_id, force=force)


@task_app.command(comment_cmd_instance.name, help=comment_cmd_instance.description)
def comment_task(
    task_id: str = typer.Argument(..., help="要评论的 Task ID"),
    comment: str = typer.Option(..., "--comment", "-c", help="要添加的评论"),
):
    """Typer 回调，调用 CommentTaskCommand 的 execute 方法"""
    comment_cmd_instance.execute(task_id=task_id, comment=comment)


@task_app.command(link_cmd_instance.name, help=link_cmd_instance.description)
def link_task(
    task_id: str = typer.Argument(..., help="要关联的 Task ID"),
    link_type: LinkType = typer.Option(..., "--type", "-t", help="要关联的目标实体类型", case_sensitive=False),
    target_id: str = typer.Option(..., "--target", "-id", help="目标实体的 ID 或标识符 ('-' 表示取消关联)"),
):
    """Typer 回调，调用 LinkTaskCommand 的 execute 方法"""
    link_cmd_instance.execute(task_id=task_id, link_type=link_type, target_id=target_id)


# 其他命令的注册...
# @task_app.command(...)
# def show_task(...):
#    show_cmd_instance.execute(...)

# 导出 Typer 应用，供主 CLI 使用
__all__ = ["task_app"]
