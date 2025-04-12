"""
任务命令模块 (Click 版本)

处理任务相关的命令，包括创建、查询、更新和删除操作。
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import click
import yaml
from rich.console import Console

from src.cli.decorators import pass_service
from src.models.db.task import Task
from src.services.task_service import TaskService

from .core.comment import CommentTaskCommand

# 导入 task_typer 实现
from .core.create import CreateTaskCommand
from .core.delete import DeleteTaskCommand
from .core.link import LinkTaskCommand
from .core.list import ListTaskCommand
from .core.show import ShowTaskCommand
from .core.update import UpdateTaskCommand

console = Console()
logger = logging.getLogger(__name__)


class TaskYAMLFormatter:
    """任务YAML格式化器"""

    @staticmethod
    def format_value(value):
        """格式化值

        Args:
            value: 要格式化的值

        Returns:
            格式化后的值
        """
        if value is None:
            return "-"  # 统一使用'-'表示空值
        if isinstance(value, list) and not value:
            return "-"  # 空列表也用'-'表示
        return value

    def to_yaml(self, task: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
        """转换任务为YAML格式

        Args:
            task: 任务数据
            verbose: 是否显示详细信息

        Returns:
            格式化后的任务数据
        """
        # 基础字段
        data = {
            "id": task.get("id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "assignee": self.format_value(task.get("assignee")),
        }

        # 详细信息
        if verbose:
            data.update(
                {
                    "description": self.format_value(task.get("description")),
                    "labels": self.format_value(task.get("labels")),
                    "story_id": self.format_value(task.get("story_id")),
                    "created_at": str(task.get("created_at", "-")),
                    "updated_at": str(task.get("updated_at", "-")),
                }
            )

        return data


def setup_yaml_formatter():
    """设置YAML格式化器"""

    def none_presenter(dumper, _):
        """处理None值"""
        return dumper.represent_scalar("tag:yaml.org,2002:null", "-")

    yaml.add_representer(type(None), none_presenter)


# 初始化YAML格式化器
setup_yaml_formatter()
_formatter = TaskYAMLFormatter()


def format_output(data: Union[Dict, List], format: str = "yaml", verbose: bool = False) -> str:
    """格式化输出数据

    Args:
        data: 要格式化的数据
        format: 输出格式 (yaml/json)
        verbose: 是否显示详细信息

    Returns:
        格式化后的字符串
    """
    if isinstance(data, list):
        formatted_data = [_formatter.to_yaml(item, verbose) for item in data]
    else:
        formatted_data = _formatter.to_yaml(data, verbose)

    if format == "json":
        return json.dumps(formatted_data, indent=2, ensure_ascii=False)
    return yaml.dump(formatted_data, allow_unicode=True, sort_keys=False)


def find_task_by_id_or_name(service: TaskService, id_or_name: str) -> Optional[Dict]:
    """通过ID或名称查找任务

    Args:
        service: 任务服务实例
        id_or_name: 任务ID或名称

    Returns:
        任务信息或None
    """
    # 首先尝试通过ID查找
    task = service.get_task(id_or_name)
    if task:
        return task

    # 如果找不到，尝试通过名称查找
    tasks = service.list_tasks()
    for t in tasks:
        if t["title"].lower() == id_or_name.lower():
            return t
    return None


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
        # 创建 ListTaskCommand 实例
        cmd = ListTaskCommand()

        # 调用 task_typer 的实现
        result = cmd.execute(
            status_list=list(status) if status else None,
            assignee=assignee,
            labels=list(label) if label else None,
            story_id=story,
            is_independent=independent if independent else None,
            limit=limit,
            offset=offset,
            verbose=verbose,
            format=format,
        )

        # 处理执行结果
        if result["status"] == "success":
            if not result.get("data"):
                console.print("[yellow]未找到符合条件的任务。[/yellow]")
                return 0

            # 使用原有的格式化输出
            if format.lower() == "json":
                print(json.dumps(result["data"], ensure_ascii=False, indent=2))
            else:  # 默认使用YAML
                print(yaml.safe_dump(result["data"], allow_unicode=True, sort_keys=False))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


@task.command(name="show", help="显示任务详情")
@click.argument("id_or_name")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
@pass_service(service_type="task")
def show_task(service, id_or_name: str, verbose: bool, format: str) -> None:
    """显示任务详情"""
    try:
        # 创建 ShowTaskCommand 实例
        cmd = ShowTaskCommand()

        # 调用 task_typer 的实现
        result = cmd.execute(task_id=id_or_name, verbose=verbose, format=format)

        # 处理执行结果
        if result["status"] == "success":
            if not result.get("data"):
                console.print(f"[bold red]错误:[/bold red] 找不到任务: {id_or_name}")
                return 1

            # 输出任务详情
            print(format_output(result["data"], format=format, verbose=verbose))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        if verbose:
            logger.error(f"显示任务详情时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


@task.command(name="create", help="创建新任务")
@click.option("--title", "-t", required=True, help="任务标题")
@click.option("--desc", "-d", help="任务描述")
@click.option("--labels", "-l", help="标签(逗号分隔)")
@click.option("--assignee", "-a", help="负责人")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium", help="优先级")
@click.option("--force", "-f", is_flag=True, help="强制创建(覆盖同名任务)")
@pass_service(service_type="task")
def create_task(service, title: str, desc: str = None, labels: str = None, assignee: str = None, priority: str = "medium", force: bool = False):
    """创建新任务"""
    try:
        # 创建 CreateTaskCommand 实例
        cmd = CreateTaskCommand()

        # 转换参数格式
        label_list = [l.strip() for l in labels.split(",")] if labels else None

        # 调用 task_typer 的实现
        result = cmd.execute(
            title=title, description=desc, assignee=assignee, label=label_list, status="open", priority=priority, force=force  # 默认状态
        )

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                print(format_output(result["data"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except ValueError as e:
        console.print(f"[bold red]错误:[/bold red] {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"创建任务时出错: {str(e)}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {str(e)}")
        return 1


@task.command(name="update", help="更新任务")
@click.argument("task_id")
@click.option("--title", "-t", help="新标题")
@click.option("--desc", "-d", help="新描述")
@click.option("--status", "-s", type=click.Choice(["todo", "in_progress", "review", "done", "blocked"]), help="新状态")
@click.option("--assignee", "-a", help="新负责人")
@click.option("--add-labels", "-al", help="添加标签(逗号分隔)")
@click.option("--remove-labels", "-rl", help="移除标签(逗号分隔)")
@click.option("--force", "-f", is_flag=True, help="强制更新")
@pass_service(service_type="task")
def update_task(
    service,
    task_id: str,
    title: str = None,
    desc: str = None,
    status: str = None,
    assignee: str = None,
    add_labels: str = None,
    remove_labels: str = None,
    force: bool = False,
):
    """更新任务"""
    try:
        # 创建 UpdateTaskCommand 实例
        cmd = UpdateTaskCommand()

        # 处理标签
        add_label_list = [l.strip() for l in add_labels.split(",")] if add_labels else None
        remove_label_list = [l.strip() for l in remove_labels.split(",")] if remove_labels else None

        # 调用 task_typer 的实现
        result = cmd.execute(
            task_id=task_id,
            title=title,
            description=desc,
            status=status,
            assignee=assignee,
            add_labels=add_label_list,
            remove_labels=remove_label_list,
            force=force,
        )

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                print("\n更新后的任务详情:")
                print(format_output(result["data"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except ValueError as e:
        console.print(f"[bold red]错误:[/bold red] {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"更新任务时出错: {str(e)}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {str(e)}")
        return 1


@task.command(name="delete", help="删除任务")
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="跳过确认直接删除")
@pass_service(service_type="task")
def delete_task(service, task_id: str, force: bool) -> None:
    """删除任务"""
    try:
        # 创建 DeleteTaskCommand 实例
        cmd = DeleteTaskCommand()

        # 调用 task_typer 的实现
        result = cmd.execute(task_id=task_id, force=force)

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"删除任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


@task.command(name="comment", help="添加任务评论")
@click.argument("task_id")
@click.option("--comment", "-c", required=True, help="要添加的评论")
@pass_service(service_type="task")
def comment_task(service, task_id: str, comment: str) -> None:
    """添加任务评论"""
    try:
        # 创建 CommentTaskCommand 实例
        cmd = CommentTaskCommand()

        # 调用 task_typer 的实现
        result = cmd.execute(task_id=task_id, comment=comment)

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                print("\n评论详情:")
                print(format_output(result["data"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"为任务 {task_id} 添加评论时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


@task.command(name="link", help="关联任务")
@click.argument("task_id")
@click.option("--type", "-t", type=click.Choice(["story", "session", "github"]), required=True, help="关联类型")
@click.option("--target", "-id", required=True, help="目标ID (如果是'-'则解除关联)")
@pass_service(service_type="task")
def link_task(service, task_id: str, type: str, target: str) -> None:
    """关联任务到Story、工作流会话或GitHub Issue"""
    try:
        # 创建 LinkTaskCommand 实例
        cmd = LinkTaskCommand()

        # 调用 task_typer 的实现
        result = cmd.execute(task_id=task_id, link_type=type, target_id=target)

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                print("\n关联后的任务详情:")
                print(format_output(result["data"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"关联任务 {task_id} 时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1
