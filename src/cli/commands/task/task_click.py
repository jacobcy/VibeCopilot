"""
任务命令模块 (Click 版本)

处理任务相关的命令，包括创建、查询、更新和删除操作。
"""

import json
import logging
from typing import Dict, List, Optional

import click
import yaml
from rich.console import Console
from src.cli.decorators import pass_service
from src.models.db.task import Task
from src.services.task_service import TaskService

from .link_type import LinkType

console = Console()
logger = logging.getLogger(__name__)


@click.group(help="任务管理命令 (类似 GitHub issue)")
def task():
    """任务管理命令组"""
    pass


@task.command(name="list", help="列出项目中的任务")
@click.option("--status", "-s", multiple=True, help="按状态过滤 (例如: open,in_progress)")
@click.option("--assignee", "-a", help="按负责人过滤")
@click.option("--label", "-l", multiple=True, help="按标签过滤 (目前仅简单匹配)")
@click.option("--story", "-r", help="按关联的Story ID过滤")
@click.option("--independent", "-i", is_flag=True, help="仅显示独立任务 (无Story关联)")
@click.option("--limit", type=int, help="限制返回数量")
@click.option("--offset", type=int, help="跳过指定数量的结果")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
@pass_service(service_type="task")
def list_tasks(
    service,
    status: List[str],
    assignee: Optional[str],
    label: List[str],
    story: Optional[str],
    independent: bool,
    limit: Optional[int],
    offset: Optional[int],
    verbose: bool,
    format: str,
) -> None:
    """列出任务"""
    try:
        # 将status和label转换为可能为None的列表
        status_list = list(status) if status else None
        label_list = list(label) if label else None

        # 使用任务服务列出任务
        tasks = service.list_tasks(
            status=status_list,
            assignee=assignee,
            labels=label_list,
            story_id=story,
            is_independent=independent if independent else None,
            limit=limit,
            offset=offset,
        )

        if not tasks:
            console.print("[yellow]未找到符合条件的任务。[/yellow]")
            return

        # 准备输出数据
        output_data = []

        # 根据是否详细模式选择包含的字段
        for task in tasks:
            # 确保task是字典，如果是Task对象则调用to_dict()
            if hasattr(task, "to_dict"):
                task = task.to_dict()

            task_info = {
                "id": task.get("id", "unknown"),
                "title": task.get("title", ""),
                "status": task.get("status", "unknown"),
                "assignee": task.get("assignee") if task.get("assignee") else "-",
            }

            if verbose:
                # 详细模式包含更多信息
                task_info.update(
                    {
                        "description": task.get("description", ""),
                        "story_id": task.get("story_id", "-"),
                        "labels": task.get("labels", []),
                        "created_at": str(task.get("created_at", "-")),
                        "updated_at": str(task.get("updated_at", "-")),
                    }
                )

            output_data.append(task_info)

        # 根据指定格式输出
        if format.lower() == "json":
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
        else:  # 默认使用YAML
            print(yaml.safe_dump(output_data, allow_unicode=True, sort_keys=False))

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="show", help="显示任务详细信息")
@click.argument("task_id")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息，包括评论")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
@pass_service(service_type="task")
def show_task(service, task_id: str, verbose: bool, format: str) -> None:
    """显示任务详情"""
    try:
        # 获取任务信息
        task = service.get_task(task_id)

        if not task:
            console.print(f"[bold red]错误:[/bold red] 找不到任务: {task_id}")
            return

        # 格式化输出
        if format.lower() == "json":
            print(json.dumps(task, ensure_ascii=False, indent=2))
        else:  # 默认使用YAML
            print(yaml.safe_dump(task, allow_unicode=True, sort_keys=False))

    except Exception as e:
        logger.error(f"显示任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="create", help="创建新任务")
@click.option("--title", "-t", required=True, help="任务标题 (必需)")
@click.option("--desc", "-d", help="任务描述")
@click.option("--assignee", "-a", help="负责人")
@click.option("--label", "-l", multiple=True, help="标签 (多个标签用多次选项)")
@click.option("--status", "-s", default="open", help="初始状态 (默认: open)")
@click.option("--link-story", help="关联到Story (成为路线图的一部分)")
@click.option("--link-github", help="关联到GitHub Issue (格式: owner/repo#number)")
@pass_service(service_type="task")
def create_task(
    service,
    title: str,
    desc: Optional[str],
    assignee: Optional[str],
    label: List[str],
    status: str,
    link_story: Optional[str],
    link_github: Optional[str],
) -> None:
    """创建任务"""
    try:
        task_data = {
            "title": title,
            "description": desc,
            "assignee": assignee,
            "labels": list(label) if label else None,
            "status": status,
            "story_id": link_story,
        }

        # --- 解析并处理 GitHub 链接 ---
        github_issue_number = None
        if link_github:
            try:
                if "#" not in link_github or "/" not in link_github.split("#")[0]:
                    raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
                repo_part, issue_num_str = link_github.split("#", 1)
                github_issue_number = int(issue_num_str)
                task_data["github_issue_number"] = github_issue_number
                logger.info(f"解析到 GitHub Issue 编号: {github_issue_number} (仓库: {repo_part})")
            except ValueError as e:
                console.print(f"[bold red]错误:[/bold red] 无效的 GitHub 链接格式: {e}")
                return
            except Exception as e:
                logger.error(f"解析 GitHub 链接时出错: {e}", exc_info=True)
                console.print(f"[bold red]错误:[/bold red] 解析 GitHub 链接时出错: {e}")
                return

        # 使用任务服务创建任务
        new_task = service.create_task(task_data)

        if not new_task:
            console.print("[bold red]错误:[/bold red] 创建任务失败")
            return

        console.print(f"[bold green]成功:[/bold green] 已创建任务 '{new_task['title']}' (ID: {new_task['id']})")

    except ValueError as ve:
        logger.error(f"创建任务时数据验证失败: {ve}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {ve}")
    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="update", help="更新任务信息")
@click.argument("task_id")
@click.option("--title", "-t", help="新的任务标题")
@click.option("--desc", "-d", help="新的任务描述")
@click.option("--assignee", "-a", help="新的负责人 ('-' 表示清空)")
@click.option("--label", "-l", multiple=True, help="设置新的标签列表 (覆盖旧列表)")
@click.option("--add-label", multiple=True, help="添加标签")
@click.option("--remove-label", multiple=True, help="移除标签")
@click.option("--status", "-s", help="新的状态")
@pass_service(service_type="task")
def update_task(
    service,
    task_id: str,
    title: Optional[str],
    desc: Optional[str],
    assignee: Optional[str],
    label: List[str],
    add_label: List[str],
    remove_label: List[str],
    status: Optional[str],
) -> None:
    """更新任务"""
    try:
        # 准备更新数据
        update_data = {}

        if title is not None:
            update_data["title"] = title

        if desc is not None:
            update_data["description"] = desc

        if assignee is not None:
            # 特殊处理：'-' 表示清空assignee
            update_data["assignee"] = None if assignee == "-" else assignee

        if label:
            # 如果提供了label选项，将替换现有标签
            update_data["labels"] = list(label)

        if status is not None:
            update_data["status"] = status

        # 获取现有任务，用于处理标签添加/删除
        if add_label or remove_label:
            existing_task = service.get_task(task_id)
            if not existing_task:
                console.print(f"[bold red]错误:[/bold red] 找不到任务: {task_id}")
                return

            current_labels = existing_task.get("labels", [])

            # 处理标签添加
            if add_label:
                for lbl in add_label:
                    if lbl not in current_labels:
                        current_labels.append(lbl)

            # 处理标签删除
            if remove_label:
                current_labels = [lbl for lbl in current_labels if lbl not in remove_label]

            # 更新标签
            update_data["labels"] = current_labels

        # 执行更新
        updated_task = service.update_task(task_id, update_data)

        if not updated_task:
            console.print(f"[bold red]错误:[/bold red] 更新任务失败: {task_id}")
            return

        console.print(f"[bold green]成功:[/bold green] 已更新任务 '{updated_task['title']}' (ID: {updated_task['id']})")

    except Exception as e:
        logger.error(f"更新任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="delete", help="删除任务")
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="跳过确认直接删除")
@pass_service(service_type="task")
def delete_task(service, task_id: str, force: bool) -> None:
    """删除任务"""
    try:
        # 获取任务以显示信息
        task = service.get_task(task_id)
        if not task:
            console.print(f"[bold red]错误:[/bold red] 找不到任务: {task_id}")
            return

        # 如果需要确认且不是强制删除
        if not force:
            # 显示任务信息并请求确认
            console.print(f"将删除任务: [bold]{task['title']}[/bold] (ID: {task_id})")
            if not click.confirm("确定要删除这个任务吗?"):
                console.print("已取消删除操作")
                return

        # 执行删除
        success = service.delete_task(task_id)

        if success:
            console.print(f"[bold green]成功:[/bold green] 已删除任务 '{task['title']}' (ID: {task_id})")
        else:
            console.print(f"[bold red]错误:[/bold red] 删除任务失败: {task_id}")

    except Exception as e:
        logger.error(f"删除任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="comment", help="添加任务评论")
@click.argument("task_id")
@click.option("--comment", "-c", required=True, help="要添加的评论")
@pass_service(service_type="task")
def comment_task(service, task_id: str, comment: str) -> None:
    """添加任务评论"""
    try:
        # 添加评论
        result = service.add_comment(task_id, comment)

        if result and "id" in result:
            console.print(f"[bold green]成功:[/bold green] 已添加评论到任务 (ID: {task_id})")
        else:
            console.print(f"[bold red]错误:[/bold red] 添加评论失败")

    except Exception as e:
        logger.error(f"为任务 {task_id} 添加评论时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")


@task.command(name="link", help="关联任务")
@click.argument("task_id")
@click.option("--type", "-t", type=click.Choice(["story", "session", "github"]), required=True, help="关联类型")
@click.option("--target", "-id", required=True, help="目标ID (如果是'-'则解除关联)")
@pass_service(service_type="task")
def link_task(service, task_id: str, type: str, target: str) -> None:
    """关联任务到Story、工作流会话或GitHub Issue"""
    try:
        # 转换为枚举类型
        link_type = type

        # 处理特殊情况：取消关联
        if target == "-":
            target = None

        # 获取任务
        task = service.get_task(task_id)
        if not task:
            console.print(f"[bold red]错误:[/bold red] 找不到任务: {task_id}")
            return

        # 根据类型更新任务
        update_data = {}

        if link_type == "story":
            update_data["story_id"] = target
            type_desc = "Story"
        elif link_type == "session":
            update_data["workflow_session_id"] = target
            type_desc = "工作流会话"
        elif link_type == "github":
            if target:
                # 解析GitHub链接
                try:
                    if "#" not in target or "/" not in target.split("#")[0]:
                        raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
                    repo_part, issue_num_str = target.split("#", 1)
                    github_issue_number = int(issue_num_str)
                    update_data["github_issue_number"] = github_issue_number
                except ValueError as e:
                    console.print(f"[bold red]错误:[/bold red] 无效的 GitHub 链接格式: {e}")
                    return
            else:
                update_data["github_issue_number"] = None
            type_desc = "GitHub Issue"

        # 执行更新
        updated_task = service.update_task(task_id, update_data)

        if updated_task:
            if target:
                console.print(f"[bold green]成功:[/bold green] 已将任务 '{task['title']}' 关联到 {type_desc}: {target}")
            else:
                console.print(f"[bold green]成功:[/bold green] 已解除任务 '{task['title']}' 与 {type_desc} 的关联")
        else:
            console.print(f"[bold red]错误:[/bold red] 关联任务失败")

    except Exception as e:
        logger.error(f"关联任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
