# src/cli/commands/task/core/list.py

import logging
import re  # 导入 re 模块
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from src.db.session_manager import session_scope
from src.services.task.core import TaskService

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="list", help="列出项目中的任务")
@click.option("--status", "-s", multiple=True, help="按状态过滤 (例如: open,in_progress)")
@click.option("--assignee", "-a", help="按负责人过滤")
@click.option("--label", "-l", multiple=True, help="按标签过滤 (目前仅简单匹配)")
@click.option("--roadmap", "-r", help="按关联的 Story ID 过滤")
@click.option("--independent", "-i", is_flag=True, help="仅显示独立任务 (无 Story 关联)")
@click.option("--temp", "-t", type=click.Choice(["yes", "no", "all"]), default="all", help="过滤临时任务 (yes: 仅显示临时任务, no: 仅显示有 Story 关联的任务, all: 显示所有任务)")
@click.option("--limit", type=int, help="限制返回数量")
@click.option("--offset", type=int, help="跳过指定数量的结果")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息")
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
def list_tasks(
    status: List[str],
    assignee: Optional[str],
    label: List[str],
    roadmap: Optional[str],
    independent: bool,
    temp: str,
    limit: Optional[int],
    offset: Optional[int],
    verbose: bool,
    format: str,
) -> None:
    """列出项目中的任务

    用于列出和过滤项目中的任务。支持按状态、负责人、标签等条件过滤，
    并可以通过 --verbose 选项显示更详细的任务信息。
    输出格式为带状态高亮的类 YAML 格式。
    """
    try:
        result = execute_list_tasks(
            status=list(status) if status else None,
            assignee=assignee,
            label=list(label) if label else None,
            story_id=roadmap,
            independent=independent,
            temp=temp,
            limit=limit,
            offset=offset,
            verbose=verbose,
            format=format,
        )

        if result["status"] == "success":
            if not result.get("data"):
                console.print("[yellow]未找到符合条件的任务。[/yellow]")
                return

            # --- 创建任务表格 ---
            status_colors = {
                "todo": "yellow",
                "backlog": "bright_black",
                "in_progress": "blue",
                "review": "cyan",
                "done": "green",
                "closed": "bright_green",
                "blocked": "red",
            }
            default_color = "white"  # 未知状态的颜色

            # 创建表格
            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1, 0, 1))
            table.add_column("编号", style="dim", justify="right")
            table.add_column("标题", style="bold")
            table.add_column("状态", justify="center")

            # 添加可选列
            if verbose:
                table.add_column("ID", style="dim")
                table.add_column("创建时间", style="dim")

            # 填充表格数据
            tasks_data = result["data"]

            # 组织任务数据 - 按story_id分组
            tasks_by_story = {}
            independent_tasks = []

            for task in tasks_data:
                story_id = task.get("story_id")
                if story_id:
                    if story_id not in tasks_by_story:
                        tasks_by_story[story_id] = []
                    tasks_by_story[story_id].append(task)
                else:
                    independent_tasks.append(task)

            # 处理独立任务和按story分组的任务
            display_tasks = []

            # 先处理按story分组的任务
            story_counter = 1
            for story_id, tasks in tasks_by_story.items():
                # 按照local_display_number排序任务
                sorted_tasks = sorted(tasks, key=lambda x: x.get("local_display_number", ""))
                # 为每个任务分配层级编号
                task_counter = 1
                for task in sorted_tasks:
                    # 创建层级编号 story_num.task_num
                    hierarchical_number = f"{story_counter}.{task_counter}"
                    task["hierarchical_number"] = hierarchical_number
                    display_tasks.append(task)
                    task_counter += 1
                story_counter += 1

            # 再处理独立任务
            for i, task in enumerate(independent_tasks):
                # 独立任务使用单一编号
                task["hierarchical_number"] = f"{i+1}"
                display_tasks.append(task)

            # 添加任务行到表格
            for task in display_tasks:
                # 获取状态和对应颜色
                status_value = task.get("status", "unknown")
                color = status_colors.get(status_value, default_color)

                # 获取显示编号和标题
                display_number = task.get("hierarchical_number", "")
                title = task.get("title", "")
                task_id = task.get("id", "")
                created_at = task.get("created_at", "")

                # 简化创建时间，仅保留日期部分
                if created_at and len(created_at) > 10:
                    created_at = created_at[:10]

                # 根据是否显示详细信息添加行
                if verbose:
                    table.add_row(f"#{display_number}" if display_number else "", title, f"[{color}]{status_value}[/{color}]", task_id, created_at)
                else:
                    table.add_row(f"#{display_number}" if display_number else "", title, f"[{color}]{status_value}[/{color}]")

            # 打印表格
            console.print(table)

            # 打印简短的使用说明
            console.print("\n[dim]提示: 使用 'vc task show #编号' 查看详细信息[/dim]")

            return  # 成功完成
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            # return 1 # 由 click 框架处理退出码

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        # return 1 # 由 click 框架处理退出码


def execute_list_tasks(
    status: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    story_id: Optional[str] = None,
    independent: Optional[bool] = None,
    temp: Optional[str] = "all",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    verbose: bool = False,
    format: str = "yaml",
) -> Dict[str, Any]:
    """执行列出任务的核心逻辑"""
    logger.info(
        f"执行任务列表命令: status={status}, assignee={assignee}, label={label}, "
        f"story_id={story_id}, independent={independent}, temp={temp}, "
        f"limit={limit}, offset={offset}, verbose={verbose}, format={format}"
    )

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": [],
        "meta": {"command": "task list", "args": locals()},
    }

    # 处理独立任务过滤参数
    is_independent_filter = None
    if independent is True:
        is_independent_filter = True
    elif independent is False:
        is_independent_filter = False

    # 处理临时任务过滤参数
    is_temporary_filter = None
    if temp == "yes":
        is_temporary_filter = True
    elif temp == "no":
        is_temporary_filter = False
    # "all" 不设置过滤条件

    try:
        # 使用TaskService获取任务列表
        with session_scope() as session:
            task_service = TaskService()

            # 构建查询参数
            query_params = {
                "session": session,
                "status": status,
                "assignee": assignee,
                "labels": label,
                "story_id": story_id,
                "is_independent": is_independent_filter,
                "is_temporary": is_temporary_filter,
                "limit": limit,
                "offset": offset,
            }

            # 使用TaskService的公共方法
            tasks = task_service.search_tasks(**query_params)

            if not tasks:
                results["message"] = "未找到符合条件的任务。"
                return results

            # 转换任务列表为只包含关键信息的字典格式
            refined_task_dicts = []
            for task in tasks:
                refined_dict = {
                    "id": task.get("id"),
                    "local_display_number": task.get("local_display_number"),
                    "story_id": task.get("story_id"),  # 添加story_id用于任务分组
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "status": task.get("status"),
                    "memory_references": task.get("memory_references", []),
                    "created_at": task.get("created_at"),
                }
                refined_task_dicts.append(refined_dict)

            results["data"] = refined_task_dicts
            results["message"] = f"成功检索到 {len(refined_task_dicts)} 个任务"

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"列出任务时出错: {e}"

    return results
