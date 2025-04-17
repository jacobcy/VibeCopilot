# src/cli/commands/task/core/create.py

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from loguru import logger
from rich.console import Console

from src.core.config import get_config
from src.db.session_manager import session_scope
from src.memory import get_memory_service
from src.services.task import TaskService

console = Console()


@click.command(name="create", help="创建一个新的任务")
@click.option("-t", "--title", required=True, help="任务标题 (必需)")
@click.option("-d", "--desc", "--description", help="任务描述")
@click.option("-a", "--assignee", help="负责人")
@click.option("-l", "--label", multiple=True, help="标签 (可多次使用)")
@click.option("-s", "--status", default="open", help="初始状态 (默认: open)")
@click.option("-p", "--priority", type=click.Choice(["low", "medium", "high"]), default="medium", help="任务优先级")
@click.option("--due", help="截止日期 (格式: YYYY-MM-DD，默认为创建日期后3天)")
@click.option("--link-story", help="关联到Story")
@click.option("-g", "--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")
@click.option("-f", "--flow", "--workflow", help="关联到工作流类型")
@click.option("-r", "--ref", "--reference", help="关联参考文档路径")
@click.option("-v", "--verbose", is_flag=True, help="显示详细信息")
def create_task_command(
    title: str,
    desc: Optional[str],
    assignee: Optional[str],
    label: Optional[List[str]],
    status: str,
    priority: str,
    due: Optional[str],
    link_story: Optional[str],
    link_github: Optional[str],
    flow: Optional[str],
    ref: Optional[str],
    verbose: bool,
) -> int:
    """创建一个新的任务

    创建一个新的任务，支持设置标题、描述、负责人、标签等基本信息，
    以及关联到 Roadmap Item、Workflow Stage 或 GitHub Issue。

    如果不设置截止日期，将默认设置为创建日期后3天。

    可以使用--ref或--reference指定参考文档路径，该文档将被关联到任务。
    """
    try:
        # 执行创建任务的逻辑
        result = execute_create_task(
            title=title,
            description=desc,
            assignee=assignee,
            label=list(label) if label else None,
            status=status,
            priority=priority,
            due_date=due,
            link_story=link_story,
            link_github_issue=link_github,
            flow=flow,
            ref_path=ref,
            verbose=verbose,
        )

        # 输出结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("task"):
                # 使用task_click模块中的format_output函数格式化输出
                from src.cli.commands.task.task_click import format_output

                print(format_output(result["task"], format="yaml", verbose=verbose))

            # Print warnings if any
            if warnings := result.get("warnings"):
                console.print("[bold yellow]警告:[/bold yellow]")
                for warning in warnings:
                    console.print(f"- {warning}")

            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_create_task(
    title: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    status: Optional[str] = "open",
    priority: Optional[str] = "medium",
    due_date: Optional[str] = None,
    link_story: Optional[str] = None,
    link_github_issue: Optional[str] = None,
    flow: Optional[str] = None,
    ref_path: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """执行创建任务的核心逻辑"""
    logger.info(
        f"执行创建任务命令: title='{title}', assignee={assignee}, "
        f"labels={label}, status={status}, due_date={due_date}, "
        f"link_story={link_story}, "
        f"link_github={link_github_issue}, flow={flow}, "
        f"ref_path={ref_path}"
    )

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "task": None,
        "meta": {
            "command": "task create",
            "args": locals(),
        },
        "warnings": [],
    }

    if not assignee:
        assignee = "AI Agent"
        logger.info(f"没有指定负责人，默认设置为: {assignee}")

    config = get_config()
    github_owner = config.get("github.owner", None)
    logger.info(f"任务负责人: {github_owner or '未设置'}")

    task_data = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "labels": label,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "story_id": link_story,
    }

    github_issue_number = None
    if link_github_issue:
        try:
            if "#" not in link_github_issue or "/" not in link_github_issue.split("#")[0]:
                raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
            repo_part, issue_num_str = link_github_issue.split("#", 1)
            github_issue_number = int(issue_num_str)
            task_data["github_repo"] = repo_part
            task_data["github_issue_number"] = github_issue_number
            logger.info(f"解析到 GitHub Issue 编号: {github_issue_number} (仓库: {repo_part})")
        except ValueError as e:
            results["status"] = "error"
            results["code"] = 400
            results["message"] = f"无效的 GitHub 链接格式: {e}"
            console.print(f"[bold red]错误:[/bold red] 无效的 GitHub 链接格式: {e}")
            return results
        except Exception as e:
            logger.error(f"解析 GitHub 链接时出错: {e}", exc_info=True)
            console.print(f"[bold red]错误:[/bold red] 解析 GitHub 链接时出错: {e}")
            return results

    try:
        with session_scope() as session:
            task_service = TaskService()
            memory_service = get_memory_service()

            # 修正TaskService.create_task调用方式，传递task_data参数
            new_task_orm = task_service.create_task(session, task_data=task_data)

            if not new_task_orm or not getattr(new_task_orm, "id", None):
                raise Exception("TaskService did not return a valid task object after creation.")

            # 转换任务对象为字典以便后续使用
            new_task_dict = (
                new_task_orm.to_dict()
                if hasattr(new_task_orm, "to_dict")
                else {
                    key: getattr(new_task_orm, key)
                    for key in dir(new_task_orm)
                    if not key.startswith("_") and not callable(getattr(new_task_orm, key))
                }
            )

            # 获取任务ID和标题
            task_id = str(new_task_orm.id)  # 确保是字符串类型
            task_title = getattr(new_task_orm, "title", "未知任务")

            results["task"] = new_task_dict
            results["message"] = f"成功创建任务 (ID: {task_id})"
            console.print(f"[bold green]成功:[/bold green] 已创建任务 '{task_title}' (ID: {task_id})")

            try:
                log_details = {k: v for k, v in new_task_dict.items() if v is not None}
                if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                    task_service.log_task_activity(session, task_id, "任务创建", details=log_details)
                else:
                    logger.warning("TaskService does not have log_task_activity method. Skipping log.")
                    results["warnings"].append("无法记录任务创建日志 (TaskService 功能缺失)")
            except Exception as log_e:
                logger.error(f"记录任务创建日志时出错: {log_e}", exc_info=True)
                results["warnings"].append(f"记录任务创建日志时出错: {log_e}")

            if ref_path:
                try:
                    logger.info(f"尝试存储参考文档到Memory: {ref_path}")
                    ref_file = Path(ref_path)
                    if not ref_file.is_file():
                        raise FileNotFoundError(f"参考文件未找到: {ref_path}")

                    content = ref_file.read_text(encoding="utf-8")
                    note_title = f"Task Ref: {task_title} - {ref_file.name}"
                    tags_str = f"task:{task_id},type:reference"

                    mem_success, mem_msg, mem_data = memory_service.create_note(
                        content=content, title=note_title, folder="task_references", tags=tags_str
                    )

                    if mem_success:
                        permalink = mem_data.get("permalink")
                        if permalink:
                            logger.info(f"成功存储参考文档到 Memory: {permalink}")
                            update_result_dict = task_service.update_task(session, task_id, {"memory_link": permalink})
                            if update_result_dict:
                                logger.info(f"成功更新任务 {task_id} 以关联 Memory 笔记: {permalink}")
                                results["task"]["memory_link"] = permalink
                                if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                                    task_service.log_task_activity(
                                        session, task_id, "关联参考文档", details={"ref_path": ref_path, "memory_link": permalink}
                                    )
                                else:
                                    results["warnings"].append("无法记录参考文档关联日志 (TaskService 功能缺失)")
                            else:
                                logger.warning(f"更新任务 {task_id} 以关联 Memory 笔记失败")
                                results["warnings"].append(f"关联 Memory 笔记失败 (任务更新失败)")
                        else:
                            logger.warning("MemoryService.create_note 成功但未返回 permalink")
                            results["warnings"].append("存储参考文档成功但未获取到链接")
                    else:
                        logger.warning(f"存储参考文档到Memory失败: {mem_msg}")
                        results["warnings"].append(f"参考文档存储失败: {mem_msg}")

                except FileNotFoundError as fnf_e:
                    logger.warning(f"参考文件处理失败: {fnf_e}")
                    results["warnings"].append(f"参考文件处理失败: {fnf_e}")
                except Exception as ref_e:
                    logger.error(f"处理参考文档时出错: {str(ref_e)}", exc_info=True)
                    results["warnings"].append(f"处理参考文档时出错: {str(ref_e)}")

            if flow:
                try:
                    logger.info(f"尝试关联任务 {task_id} 到工作流 '{flow}'")
                    session_info = task_service.link_to_flow_session(session, task_id, flow_type=flow)
                    if session_info:
                        session_id = session_info.get("id")
                        session_name = session_info.get("name")
                        logger.info(f"成功关联到工作流会话 '{session_name}' (ID: {session_id})")
                        console.print(f"[bold green]成功:[/bold green] 已关联到工作流会话 '{session_name}' (ID: {session_id})")
                        results["task"]["flow_session_id"] = session_id
                        if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                            task_service.log_task_activity(
                                session, task_id, "关联到工作流", details={"flow": flow, "session_id": session_id, "session_name": session_name}
                            )
                        else:
                            results["warnings"].append("无法记录工作流关联日志 (TaskService 功能缺失)")

                    else:
                        error_message = f"关联工作流 '{flow}' 失败 (服务未返回会话信息)"
                        logger.warning(error_message)
                        results["warnings"].append(error_message)
                        console.print(f"[bold yellow]警告:[/bold yellow] {error_message}")
                        if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                            task_service.log_task_activity(session, task_id, "关联工作流失败", details={"error": error_message, "flow": flow})
                        else:
                            results["warnings"].append("无法记录工作流关联失败日志 (TaskService 功能缺失)")

                except ValueError as ve:
                    error_message = str(ve)
                    logger.warning(f"关联工作流失败: {error_message}")
                    console.print(f"[bold yellow]警告:[/bold yellow] {error_message}")
                    results["warnings"].append(f"关联工作流失败: {error_message}")
                    if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                        task_service.log_task_activity(session, task_id, "关联工作流失败", details={"error": error_message, "flow": flow})
                    else:
                        results["warnings"].append("无法记录工作流关联失败日志 (TaskService 功能缺失)")

                except Exception as e:
                    error_message = f"关联工作流时发生意外错误: {str(e)}"
                    logger.error(error_message, exc_info=True)
                    console.print(f"[bold yellow]警告:[/bold yellow] {error_message}")
                    results["warnings"].append(error_message)
                    if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                        task_service.log_task_activity(session, task_id, "关联工作流失败", details={"error": error_message, "flow": flow})
                    else:
                        results["warnings"].append("无法记录工作流关联失败日志 (TaskService 功能缺失)")

            task_service.set_current_task(session, task_id)
            if hasattr(task_service, "log_task_activity") and callable(getattr(task_service, "log_task_activity")):
                task_service.log_task_activity(session, task_id, "设置为当前任务")
            else:
                results["warnings"].append("无法记录设置为当前任务日志 (TaskService 功能缺失)")

    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"创建任务时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    if not results.get("warnings"):
        if "warnings" in results:
            del results["warnings"]

    return results
