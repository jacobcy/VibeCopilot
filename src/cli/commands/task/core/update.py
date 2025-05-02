# src/cli/commands/task/core/update.py

"""
更新任务命令模块
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from rich.console import Console

# 导入任务日志相关函数和Memory存储函数
from src.db.session_manager import session_scope
from src.memory import get_memory_service
from src.services.task import TaskService

console = Console()
logger = logging.getLogger(__name__)
# 定义有效的任务状态
VALID_TASK_STATUSES = ["todo", "in_progress", "done", "blocked", "review", "backlog"]


def parse_github_url(url: str) -> Tuple[str, int]:
    """
    解析GitHub URL，提取仓库信息和issue编号

    支持的格式:
    - https://github.com/owner/repo/issues/123
    - owner/repo#123

    Args:
        url: GitHub URL

    Returns:
        Tuple[str, int]: (仓库路径, issue编号)

    Raises:
        ValueError: 当URL格式无效时
    """
    # 尝试解析完整URL格式
    url_pattern = r"https?://github\.com/([^/]+/[^/]+)/issues/(\d+)"
    url_match = re.match(url_pattern, url)

    if url_match:
        return url_match.group(1), int(url_match.group(2))

    # 尝试解析简短格式
    short_pattern = r"([^/]+/[^#]+)#(\d+)"
    short_match = re.match(short_pattern, url)

    if short_match:
        return short_match.group(1), int(short_match.group(2))

    raise ValueError(f"无效的GitHub URL格式: {url}。支持的格式: 'owner/repo#123' 或 'https://github.com/owner/repo/issues/123'")


@click.command(name="update", help="更新现有任务的信息")
@click.argument("task_id", required=False)
@click.option("--title", "-t", help="任务标题")
@click.option("--desc", "--description", "-d", help="任务描述")
@click.option("--status", "-s", help="任务状态")
@click.option("--assignee", "-a", help="任务负责人")
@click.option("--labels", "-l", multiple=True, help="设置新的标签列表")
@click.option("--priority", "-p", type=click.Choice(["low", "medium", "high"]), help="任务优先级")
@click.option("--due", "--due-date", help="截止日期 (格式: YYYY-MM-DD，设置为'clear'可清除截止日期)")
@click.option("--link-github", "-g", help="关联的 GitHub Issue URL")
@click.option("--link-story", "-y", help="关联的故事 ID")
@click.option("--ref", "--reference", "-r", help="关联参考文档路径")
@click.option("--unlink", type=click.Choice(["story", "github"]), help="取消关联 (story 或 github)")
@click.option("--current", is_flag=True, help="将此任务设置为当前活动任务")
def update_task(
    task_id: Optional[str],
    title: Optional[str] = None,
    desc: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[Tuple[str]] = None,
    priority: Optional[str] = None,
    due: Optional[str] = None,
    link_github: Optional[str] = None,
    link_story: Optional[str] = None,
    ref: Optional[str] = None,
    unlink: Optional[str] = None,
    current: bool = False,
) -> int:
    """
    更新现有任务的信息。

    如果未提供 TASK_ID，则更新当前活动任务。
    可以使用 --current 标志将指定或当前任务设置为活动任务。

    参数:
        task_id: 要更新的任务ID (可选，默认为当前任务)
        title: 新的任务标题
        desc: 新的任务描述
        status: 新的任务状态
        assignee: 新的任务负责人
        labels: 设置新的标签列表 (覆盖现有)
        due: 新的截止日期
        link_github: 关联 GitHub Issue URL
        link_story: 关联故事 ID
        unlink: 取消关联 (story 或 github)
        current: 是否将此任务设为当前任务
    """
    try:
        # 检查是否提供了至少一个更新参数或 --current 标志
        update_args = [title, desc, status, assignee, labels, priority, due, link_github, link_story, ref, unlink]
        if not any(arg is not None and arg != () for arg in update_args) and not current:
            console.print("[bold yellow]警告:[/bold yellow] 未提供任何需要更新的字段或设置当前任务。使用 --help 查看可用选项。")
            return 1

        # 调用执行逻辑
        result = execute_update_task(
            task_id=task_id,
            title=title,
            description=desc,
            status=status,
            assignee=assignee,
            labels=list(labels) if labels else None,
            priority=priority,
            due_date=due,
            github_url=link_github,
            link_story=link_story,
            ref_path=ref,
            unlink=unlink,
            set_current=current,
        )

        # 处理执行结果
        if result["status"] == "success" or result["status"] == "warning":
            console.print(f"[bold green]结果:[/bold green] {result['message']}")
            if warnings := result.get("warnings"):
                console.print("\n[bold yellow]警告:[/bold yellow]")
                for warning in warnings:
                    console.print(f"- {warning}")
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"更新任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_update_task(
    task_id: Optional[str],
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    github_url: Optional[str] = None,
    link_story: Optional[str] = None,
    ref_path: Optional[str] = None,
    unlink: Optional[str] = None,
    set_current: bool = False,
) -> Dict[str, Any]:
    """执行更新任务的核心逻辑"""
    logger.info(f"执行更新任务命令: task_id={task_id}, set_current={set_current}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task update",
            "args": locals(),
        },
        "warnings": [],
    }

    effective_task_id = task_id
    is_updating_current = False

    task_provider = None
    try:
        from src.status.service import StatusService

        status_service = StatusService.get_instance()
        task_provider = status_service.provider_manager.get_provider("task")
    except Exception as e:
        logger.warning(f"获取 Task Provider 失败: {e}. 设置当前任务功能将不可用。")
        results["warnings"].append("状态服务异常，设置当前任务功能可能受影响。")

    if effective_task_id is None:
        is_updating_current = True
        if task_provider and hasattr(task_provider, "get_current_task_id"):
            effective_task_id = task_provider.get_current_task_id()
            if effective_task_id:
                logger.info(f"未提供任务ID，将更新当前任务: {effective_task_id}")
                console.print(f"[dim]正在更新当前任务: {effective_task_id}...[/dim]")
            else:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = "未提供任务ID，且当前没有活动任务。请使用 'vc task update <ID> --current' 设置或提供一个任务ID。"
                return results
        else:
            results["status"] = "error"
            results["code"] = 500
            results["message"] = "无法获取当前任务信息（状态服务不可用）。请提供任务ID。"
            return results

    log_updates = {}
    update_data = {}

    if title is not None:
        log_updates["标题"] = title
        update_data["title"] = title
    if description is not None:
        log_updates["描述"] = description
        update_data["description"] = description
    if status is not None:
        log_updates["状态"] = status
        update_data["status"] = status
    if assignee is not None:
        log_updates["负责人"] = assignee
        update_data["assignee"] = assignee
    if labels is not None:
        log_updates["标签"] = ", ".join(labels)
        update_data["labels"] = labels
    if priority is not None:
        log_updates["优先级"] = priority
        update_data["priority"] = priority
    if due_date is not None:
        log_updates["截止日期"] = due_date
        update_data["due_date"] = None if due_date.lower() == "clear" else due_date
    if github_url is not None:
        try:
            github_repo, github_issue_number = parse_github_url(github_url)
            log_updates["GitHub Issue"] = f"{github_repo}#{github_issue_number}"
            update_data["github_repo"] = github_repo
            update_data["github_issue_number"] = github_issue_number
        except ValueError as e:
            results["status"] = "error"
            results["code"] = 400
            results["message"] = f"GitHub URL 格式无效: {e}"
            return results
    if link_story is not None:
        log_updates["关联故事"] = link_story
        update_data["story_id"] = link_story

    if ref_path is not None:
        log_updates["参考文档"] = ref_path
    if unlink == "story":
        log_updates["取消关联故事"] = True
        update_data["story_id"] = None
    elif unlink == "github":
        log_updates["取消关联GitHub"] = True
        update_data["github_issue_number"] = None
        update_data["github_repo"] = None

    if status and status not in VALID_TASK_STATUSES:
        valid_statuses = ", ".join(VALID_TASK_STATUSES)
        results["status"] = "error"
        results["code"] = 400
        results["message"] = f"无效的任务状态: {status}。有效状态值为: {valid_statuses}"
        return results

    task_updated_successfully = False
    current_set_successfully = False

    try:
        with session_scope() as session:
            task_service = TaskService()
            memory_service = get_memory_service()

            task = task_service.get_task(session, effective_task_id)
            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"更新失败: 未找到任务 {effective_task_id}"
                return results

            original_task_data_for_log = task.copy()
            has_updates = bool(update_data)

            if has_updates:
                logger.info(f"准备更新任务 {effective_task_id} 使用数据: {update_data}")
                updated_task_dict = task_service.update_task(session, effective_task_id, update_data)

                if updated_task_dict:
                    task_updated_successfully = True
                    results["data"] = updated_task_dict
                    logger.info(f"任务 {effective_task_id} 更新成功")

                    # 处理参考文档
                    if ref_path:
                        try:
                            from pathlib import Path

                            ref_file = Path(ref_path)
                            if not ref_file.is_file():
                                results["warnings"].append(f"参考文件未找到: {ref_path}")
                            else:
                                content = ref_file.read_text(encoding="utf-8")
                                task_title = updated_task_dict.get("title", "未知任务")
                                note_title = f"Task Ref: {task_title} - {ref_file.name}"
                                tags_str = f"task:{effective_task_id},type:reference"

                                mem_success, mem_msg, mem_data = memory_service.create_note(
                                    content=content, title=note_title, folder="task_references", tags=tags_str
                                )

                                if mem_success:
                                    logger.info(f"成功存储参考文档到Memory: {ref_path}")
                                    results["data"]["reference"] = {"path": ref_path, "memory_id": mem_data.get("id")}
                                    if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                                        task_service.log_task_activity(
                                            session, effective_task_id, "添加参考文档", details={"path": ref_path, "memory_id": mem_data.get("id")}
                                        )
                                else:
                                    results["warnings"].append(f"存储参考文档到Memory失败: {mem_msg}")
                        except Exception as e:
                            logger.error(f"处理参考文档时出错: {e}", exc_info=True)
                            results["warnings"].append(f"处理参考文档时出错: {e}")
                else:
                    raise Exception(f"TaskService.update_task 未能成功更新任务 {effective_task_id}")
            elif not set_current:
                logger.info(f"没有提供需要更新的任务字段，也没有设置 --current 标志。")
                results["message"] = "没有提供需要更新的任务字段。"
                return results

            if set_current:
                logger.debug(f"检查 Task Provider: {task_provider}")
                if task_provider and hasattr(task_provider, "set_current_task"):
                    logger.debug(f"调用 Task Provider 的 set_current_task 方法，任务 ID: {effective_task_id}")
                    success = task_provider.set_current_task(effective_task_id)
                    logger.debug(f"Task Provider set_current_task 返回: {success}")
                    if success:
                        current_set_successfully = True
                        logger.info(f"任务 {effective_task_id} 已设置为当前任务。")
                    else:
                        logger.error(f"Task Provider set_current_task 方法返回 False。")
                        results["warnings"].append(f"设置任务 {effective_task_id} 为当前任务失败 (Provider 返回 False)。")
                else:
                    logger.warning("Task Provider 无效或缺少 set_current_task 方法。")
                    results["warnings"].append("无法设置当前任务（状态服务不可用或Provider无效）。")

            if task_updated_successfully and log_updates:
                try:
                    changes_for_log = {}
                    for k, v in log_updates.items():
                        original_value = original_task_data_for_log.get(k.lower().replace(" ", "_"))
                        if isinstance(original_value, list):
                            original_value = ", ".join(map(str, original_value))
                        current_value = updated_task_dict.get(k.lower().replace(" ", "_"))
                        if isinstance(current_value, list):
                            current_value = ", ".join(map(str, current_value))

                        if str(original_value) != str(current_value):
                            changes_for_log[k] = {"from": original_value, "to": v}

                    if changes_for_log:
                        if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                            task_service.log_task_activity(session, effective_task_id, "任务更新", details=changes_for_log)
                        else:
                            logger.warning("TaskService does not have log_task_activity method. Skipping log.")
                            results["warnings"].append("无法记录任务更新日志 (TaskService 功能缺失)")
                except Exception as log_e:
                    logger.error(f"记录任务更新日志时出错: {log_e}", exc_info=True)
                    results["warnings"].append(f"记录任务更新日志时出错: {log_e}")

            message_parts = []
            if task_updated_successfully:
                message_parts.append(f"任务 {effective_task_id} 更新成功。")
            if current_set_successfully:
                message_parts.append(f"任务 {effective_task_id} 已设为当前任务。")

            if not message_parts:
                if set_current and not current_set_successfully:
                    results["status"] = "warning"
                    message_parts.append(f"尝试设置任务 {effective_task_id} 为当前任务失败。")
                else:
                    message_parts.append("未执行任何操作。")

            results["message"] = " ".join(message_parts)
            if not task_updated_successfully and not current_set_successfully and set_current:
                results["status"] = "error"
            elif results["warnings"] and results["status"] == "success":
                results["status"] = "warning"

    except Exception as e:
        logger.error(f"更新任务数据库操作期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"更新任务失败: {e}"

    return results
