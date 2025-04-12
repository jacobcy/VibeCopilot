"""
任务管理命令模块

提供任务管理相关的命令实现，包括创建、查询、更新和删除操作。
"""

import click
from rich.console import Console

from .core import CommentTaskCommand, CreateTaskCommand, DeleteTaskCommand, LinkTaskCommand, ListTaskCommand, ShowTaskCommand, UpdateTaskCommand

console = Console()


@click.group(name="task", help="任务管理命令 (类似 GitHub issue)")
def task_cli():
    """任务管理命令组"""
    pass


# 实例化命令处理器
list_cmd = ListTaskCommand()
show_cmd = ShowTaskCommand()
create_cmd = CreateTaskCommand()
update_cmd = UpdateTaskCommand()
delete_cmd = DeleteTaskCommand()
comment_cmd = CommentTaskCommand()
link_cmd = LinkTaskCommand()


@task_cli.command(name="list", help="列出任务")
@click.option("--status", "-s", multiple=True, help="按状态过滤 (例如: open,in_progress)")
@click.option("--assignee", "-a", help="按负责人过滤")
@click.option("--label", "-l", multiple=True, help="按标签过滤")
@click.option("--roadmap", "-r", help="按关联的 Roadmap Item (Story ID) 过滤")
@click.option("--independent", "-i", is_flag=True, help="仅显示独立任务 (无 Roadmap 关联)")
@click.option("--limit", type=int, help="限制返回数量")
@click.option("--offset", type=int, help="跳过指定数量的结果")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息")
def list_tasks(status, assignee, label, roadmap, independent, limit, offset, verbose):
    """列出任务"""
    list_cmd.execute(
        status=status, assignee=assignee, label=label, roadmap_item_id=roadmap, independent=independent, limit=limit, offset=offset, verbose=verbose
    )


@task_cli.command(name="show", help="显示任务详情")
@click.argument("task_id")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息，包括评论")
def show_task(task_id, verbose):
    """显示任务详情"""
    show_cmd.execute(task_id=task_id, verbose=verbose)


@task_cli.command(name="create", help="创建新任务")
@click.option("--title", "-t", required=True, help="任务标题")
@click.option("--desc", "-d", help="任务描述")
@click.option("--assignee", "-a", help="负责人")
@click.option("--label", "-l", multiple=True, help="标签")
@click.option("--status", "-s", default="open", help="初始状态")
@click.option("--link-roadmap", help="关联到 Roadmap Item (Story ID)")
@click.option("--link-workflow-stage", help="关联到 Workflow Stage Instance ID")
@click.option("--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")
def create_task(title, desc, assignee, label, status, link_roadmap, link_workflow_stage, link_github):
    """创建新任务"""
    create_cmd.execute(
        title=title,
        description=desc,
        assignee=assignee,
        label=label,
        status=status,
        link_roadmap_item_id=link_roadmap,
        link_workflow_stage_instance_id=link_workflow_stage,
        link_github_issue=link_github,
    )


@task_cli.command(name="update", help="更新任务")
@click.argument("task_id")
@click.option("--title", "-t", help="新的任务标题")
@click.option("--desc", "-d", help="新的任务描述")
@click.option("--assignee", "-a", help="新的负责人 ('-' 表示清空)")
@click.option("--label", "-l", multiple=True, help="设置新的标签列表")
@click.option("--add-label", multiple=True, help="添加标签")
@click.option("--remove-label", multiple=True, help="移除标签")
@click.option("--status", "-s", help="新的状态")
def update_task(task_id, title, desc, assignee, label, add_label, remove_label, status):
    """更新任务"""
    update_cmd.execute(
        task_id=task_id, title=title, description=desc, assignee=assignee, label=label, add_label=add_label, remove_label=remove_label, status=status
    )


@task_cli.command(name="delete", help="删除任务")
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="跳过确认直接删除")
def delete_task(task_id, force):
    """删除任务"""
    delete_cmd.execute(task_id=task_id, force=force)


@task_cli.command(name="comment", help="添加任务评论")
@click.argument("task_id")
@click.option("--comment", "-c", required=True, help="要添加的评论")
def comment_task(task_id, comment):
    """添加任务评论"""
    comment_cmd.execute(task_id=task_id, comment=comment)


@task_cli.command(name="link", help="关联任务")
@click.argument("task_id")
@click.option(
    "--type",
    "-t",
    required=True,
    type=click.Choice(["roadmap", "workflow_stage", "github_issue", "github_pr", "github_commit"], case_sensitive=False),
    help="要关联的目标实体类型",
)
@click.option("--target", "-id", required=True, help="目标实体的 ID 或标识符 ('-' 表示取消关联)")
def link_task(task_id, type, target):
    """关联任务"""
    link_cmd.execute(task_id=task_id, link_type=type, target_id=target)


# 导出 Click CLI 组，供主程序使用
__all__ = ["task_cli"]
