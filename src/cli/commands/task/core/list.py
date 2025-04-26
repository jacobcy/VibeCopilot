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

            # --- 移除旧的 JSON/YAML 批量输出逻辑 ---
            # if format.lower() == "json": ...
            # else: ...

            # --- 新的逐条处理和状态高亮逻辑 ---
            status_colors = {
                "todo": "yellow",
                "backlog": "bright_black",
                "in_progress": "blue",
                "review": "cyan",
                "done": "green",
                "closed": "bright_green",  # 假设有 closed 状态
                "blocked": "red",
            }
            default_color = "white"  # 未知状态的颜色

            tasks_data = result["data"]
            for i, task_dict in enumerate(tasks_data):
                if i > 0:
                    # 在任务之间打印分隔符
                    console.print("--- -", style="dim")

                # 获取状态和对应颜色
                status_value = task_dict.get("status", "unknown")
                color = status_colors.get(status_value, default_color)

                # 将单个任务字典转为 YAML 字符串 (块状风格，增加缩进以便区分)
                try:
                    yaml_string = yaml.safe_dump(
                        task_dict, allow_unicode=True, sort_keys=False, default_flow_style=False, indent=2, width=1000  # 使用缩进  # 尽量避免自动换行
                    )
                except yaml.YAMLError as e:
                    logger.error(f"转换任务 {task_dict.get('id')} 为 YAML 时出错: {e}")
                    # 打印基础信息作为回退
                    console.print(f"id: {task_dict.get('id')}\nerror: 无法序列化任务数据")
                    continue  # 处理下一个任务

                # 查找并高亮 status 行
                highlighted_yaml_lines = []
                lines = yaml_string.splitlines()
                for line in lines:
                    # 匹配以 'status:' 开头的行 (允许前面有空格)
                    match = re.match(r"^(\s*status:\s*)(.*)$", line)
                    if match:
                        prefix = match.group(1)  # 前缀（空格和 'status: '）
                        value = match.group(2).strip()  # 原始状态值
                        # 使用 rich markup 包裹状态值
                        highlighted_line = f"{prefix}[bold {color}]{value}[/bold {color}]"
                        highlighted_yaml_lines.append(highlighted_line)
                    else:
                        highlighted_yaml_lines.append(line)

                # 使用 console.print 打印修改后的、逐行处理的字符串
                console.print("\n".join(highlighted_yaml_lines))

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

            # 使用TaskQueryService的search_tasks方法
            # tasks = task_service._query_service.search_tasks(**query_params)
            # 改为调用 TaskService 的公共方法
            tasks = task_service.search_tasks(**query_params)

            if not tasks:
                results["message"] = "未找到符合条件的任务。"
                return results

            # 转换任务列表为只包含关键信息的字典格式
            refined_task_dicts = []
            for task in tasks:
                refined_dict = {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "description": task.get("description"),
                    "status": task.get("status"),
                    "memory_references": task.get("memory_references", []),  # 确保有默认值
                }
                refined_task_dicts.append(refined_dict)

            # results["data"] = [task for task in tasks] # 旧代码
            results["data"] = refined_task_dicts  # 使用精简后的数据
            results["message"] = f"成功检索到 {len(refined_task_dicts)} 个任务"

            # --- 移除控制台表格输出 ---
            # ... (表格代码已移除)

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"列出任务时出错: {e}"
        # console.print(f"[bold red]错误:[/bold red] {e}") # 错误信息由调用者处理

    return results
