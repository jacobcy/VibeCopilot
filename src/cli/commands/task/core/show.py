# src/cli/commands/task/core/show.py

import logging
import os
import re  # 导入 re 模块用于正则表达式
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.task.utils.format import format_task_output
from src.cli.commands.task.utils.show_log import show_task_log
from src.cli.commands.task.utils.show_ref import show_task_references
from src.core.config import get_config
from src.db.session_manager import session_scope
from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


def get_relative_path(path: str) -> str:
    """获取相对于项目根目录的路径

    Args:
        path: 文件路径

    Returns:
        相对路径字符串
    """
    if not path:
        return "未知路径"

    config = get_config()
    project_root = config.get("paths.project_root", str(Path.cwd()))
    return os.path.relpath(path, project_root)


@click.command("show")
@click.argument("task_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    help="输出格式",
)
@click.option("--log", "-l", is_flag=True, help="显示任务日志")
@click.option("--ref", "-r", is_flag=True, help="显示参考资料")
@click.option("--comments", "-c", is_flag=True, help="显示评论")
@click.option("--guide", "-g", is_flag=True, help="显示执行指南")
def show(task_id: Optional[str], verbose: bool, format: str, log: bool, ref: bool, comments: bool, guide: bool) -> None:
    """显示任务详情

    如果未提供 TASK_ID，则显示当前活动任务。
    可以通过选项控制输出格式、是否显示日志、参考资料、评论和执行指南。

    TASK_ID 可以是:
    - 实际任务ID (task_12345)
    - 本地显示编号 (T1, #T1)
    - 分层编号 (1.1, #1.1) - 表示第1个story的第1个任务
    """
    try:
        result = execute_show_task(task_id, verbose, format, log, ref, comments, guide)
        if result["code"] != 0:
            raise click.ClickException(result["message"])
    except Exception as e:
        logger.error(f"显示任务失败: {e}", exc_info=True)
        raise click.ClickException(str(e))


def execute_show_task(
    task_id: Optional[str],
    verbose: bool = False,
    format: str = "yaml",
    log: bool = False,
    ref: bool = False,
    comments: bool = False,
    guide: bool = False,
) -> Dict[str, Any]:
    """执行任务显示

    Args:
        task_id: 任务ID或显示编号，支持层级编号格式(如 1.1)，如果为None，则尝试获取当前任务
        verbose: 是否显示详细信息
        format: 输出格式(json/yaml)
        log: 是否显示任务日志
        ref: 是否显示参考资料
        comments: 是否显示评论
        guide: 是否显示执行指南

    Returns:
        包含操作结果的字典
    """
    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
    }

    try:
        task = None
        task_comments = []
        current_task_id = task_id

        # --- Database Operations within session_scope ---
        with session_scope() as session:
            task_service = TaskService()

            # 如果没有提供 task_id，尝试获取当前任务
            if current_task_id is None:
                logger.info("未提供任务ID，尝试获取当前任务...")
                current_task_obj = task_service.get_current_task(session)
                if current_task_obj:
                    current_task_id = current_task_obj.get("id")
                    logger.info(f"找到当前任务: {current_task_id}")
                    console.print(f"[dim]显示当前任务: {current_task_obj.get('title', current_task_id)}[/dim]")
                else:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = "未提供任务ID，且当前没有活动任务。请使用 'vc task update --current <TASK_ID>' 设置或提供一个任务ID。"
                    return results

            # 验证 current_task_id 是否有效 (确保非 None)
            if not current_task_id:
                results["status"] = "error"
                results["code"] = 500  # Internal error, should have been caught earlier
                results["message"] = "内部错误：无法确定要显示的任务ID。"
                return results

            # 处理各种任务标识符格式
            # 1. 检查是否是层级编号格式 (1.1 或 #1.1)
            hierarchical_pattern = re.compile(r"^#?(\d+\.\d+)$")
            hierarchical_match = hierarchical_pattern.match(current_task_id)

            if hierarchical_match:
                logger.debug(f"检测到层级编号格式: {current_task_id}")
                hierarchical_number = hierarchical_match.group(1)

                # 需要通过搜索所有任务来找到匹配的层级编号
                # 因为层级编号是在列表显示时动态生成的，而不是存储在数据库中
                all_tasks = task_service.search_tasks(session=session)

                # 组织任务数据 - 按story_id分组
                tasks_by_story = {}
                independent_tasks = []

                for task in all_tasks:
                    story_id = task.get("story_id")
                    if story_id:
                        if story_id not in tasks_by_story:
                            tasks_by_story[story_id] = []
                        tasks_by_story[story_id].append(task)
                    else:
                        independent_tasks.append(task)

                # 生成层级编号并查找匹配的任务
                found_task = None

                # 处理按story分组的任务
                story_counter = 1
                for story_id, tasks in tasks_by_story.items():
                    # 按照local_display_number排序任务
                    sorted_tasks = sorted(tasks, key=lambda x: x.get("local_display_number", ""))
                    # 为每个任务分配层级编号
                    task_counter = 1
                    for task in sorted_tasks:
                        # 创建层级编号 story_num.task_num
                        task_hierarchical_number = f"{story_counter}.{task_counter}"
                        if task_hierarchical_number == hierarchical_number:
                            found_task = task
                            break
                        task_counter += 1
                    if found_task:
                        break
                    story_counter += 1

                # 如果是独立任务
                if not found_task:
                    # 独立任务使用单一编号
                    for i, task in enumerate(independent_tasks, 1):
                        if str(i) == hierarchical_number:
                            found_task = task
                            break

                if found_task:
                    current_task_id = found_task.get("id")
                    logger.info(f"通过层级编号 {hierarchical_number} 找到任务 ID: {current_task_id}")
                    task = found_task
                else:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"未找到层级编号为 {hierarchical_number} 的任务"
                    return results

            # 2. 检查是否是本地显示编号格式 (如 T1, #T1)
            elif current_task_id.startswith("#") or current_task_id.startswith("T"):
                # 尝试通过本地显示编号查找任务
                logger.debug(f"尝试使用本地显示编号查找任务: {current_task_id}")
                task = task_service.get_task_by_identifier(current_task_id)
                if task:
                    current_task_id = task.get("id")  # 更新为实际的任务ID
                    logger.info(f"成功通过本地显示编号 {current_task_id} 找到任务: {task.get('id')}")

            # 3. 直接通过ID查找
            else:
                task = task_service.get_task(session, current_task_id)

            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"任务 {current_task_id} 不存在"
                return results

            # Get comments if requested
            if comments:
                task_comments = task_service.get_task_comments(session, current_task_id)

            # 获取任务关联的工作流执行指南
            session_info = None
            if guide and task.get("current_session_id"):
                try:
                    from src.flow_session.manager import FlowSessionManager

                    session_manager = FlowSessionManager(session)
                    session_obj = session_manager.get_session(task.get("current_session_id"))
                    if session_obj:
                        session_info = session_obj.to_dict()
                except Exception as e:
                    logger.warning(f"获取执行指南失败: {e}")

        # --- Process and display results outside the session ---
        if task:
            output_content = format_task_output(task, format, verbose=True)
            if isinstance(output_content, Table):
                output_content.title = f"[bold cyan]任务详情: {task.get('title', '无标题')}[/bold cyan]"
                console.print(output_content)
            else:
                console.print(f"[bold cyan]任务详情:[/bold cyan] \n{output_content}")

            if "task_comments" in locals() and task_comments:
                console.print("\n[bold underline cyan]评论:[/bold underline cyan]")
                for comment in task_comments:
                    console.print(
                        f"[green]评论者:[/green] {comment.get('author', '匿名')} @ {comment.get('created_at', '未知时间')}\n{comment.get('content', '')}"
                    )
            elif "task_comments" in locals() and not task_comments:
                console.print("\n[dim]无评论[/dim]")

            results["data"] = task

            # Display log if requested
            if log:
                log_result = show_task_log(current_task_id, task.get("title", "未知任务"))
                if log_result["code"] != 0:
                    results["status"] = "warning"
                    results["message"] += f" 显示日志时出错: {log_result['message']}\n"

            # Display references if requested
            if ref:
                memory_link = task.get("memory_link")
                ref_result = show_task_references(current_task_id, task.get("title", "未知任务"), memory_link)
                if ref_result["code"] != 0:
                    results["status"] = "warning"
                    results["message"] += f" 显示参考时出错: {ref_result['message']}\n"

            # Display execution guide
            if guide:
                console.print("\n[bold underline]执行指南:[/bold underline]")
                if session_info:
                    try:
                        # Display basic workflow execution guide information
                        console.print(f"[cyan]工作流:[/cyan] {session_info.get('workflow_name', '未知工作流')}")
                        console.print(f"[cyan]指南名称:[/cyan] {session_info.get('name', '未命名指南')}")

                        # Get execution guide context and steps
                        from src.flow_session.core.session_context import get_context_for_session

                        context = get_context_for_session(session, session_info.get("id"))

                        if context:
                            # Display stage information
                            stage_id = context.get("current_stage")
                            if stage_id:
                                stage_info = context.get("stages", {}).get(stage_id, {})
                                console.print(f"[cyan]当前阶段:[/cyan] {stage_info.get('name', stage_id)}")

                                # Display stage description
                                stage_description = stage_info.get("description")
                                if stage_description:
                                    console.print(Panel(Markdown(stage_description), title="阶段描述", border_style="green"))

                                # Display checklist items
                                checklist = stage_info.get("checklist", [])
                                if checklist:
                                    console.print("[cyan]阶段检查项:[/cyan]")
                                    for item in checklist:
                                        status = "[green]✓[/green]" if item.get("completed") else "[yellow]⧖[/yellow]"
                                        console.print(f"  {status} {item.get('name', '未命名项')}")

                            # Display task steps
                            steps = context.get("steps", [])
                            if steps:
                                console.print("\n[cyan]执行步骤:[/cyan]")
                                for i, step in enumerate(steps, 1):
                                    console.print(f"  {i}. {step.get('name', '未命名步骤')}")

                            # Display deliverables
                            deliverables = context.get("deliverables", [])
                            if deliverables:
                                console.print("\n[cyan]交付物:[/cyan]")
                                for i, deliverable in enumerate(deliverables, 1):
                                    name = deliverable.get("name", "未命名交付物")
                                    status = deliverable.get("status", "待完成")
                                    console.print(f"  {i}. {name} - {status}")
                        else:
                            console.print("[yellow]未找到执行指南上下文[/yellow]")
                    except Exception as e:
                        logger.error(f"显示执行指南失败: {e}", exc_info=True)
                        console.print(f"[bold red]显示执行指南时出错:[/bold red] {e}")
                else:
                    console.print("[dim]此任务没有关联的执行指南[/dim]")

            # Add next steps suggestion
            console.print("\n[dim]提示: 使用 'vc task update #编号 --status=进行中' 更新任务状态[/dim]")

            # Update results with success
            results["status"] = "success"
            results["message"] = f"成功显示任务 {current_task_id} 的详情"
        else:
            # This should not happen as we already checked for task existence
            results["status"] = "error"
            results["code"] = 404
            results["message"] = f"未找到任务 {current_task_id}"

    except Exception as e:
        logger.error(f"显示任务详情时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"显示任务详情时出错: {e}"

    return results
