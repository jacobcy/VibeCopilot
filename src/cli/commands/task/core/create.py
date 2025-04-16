# src/cli/commands/task/core/create.py

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from loguru import logger
from rich.console import Console

from src.cli.commands.task.core.memory import append_to_task_log, store_ref_to_memory
from src.core.config import get_config
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.roadmap.service.roadmap_service import RoadmapService
from src.services.task import TaskService
from src.utils.file_utils import ensure_directory_exists
from src.utils.id_generator import IdGenerator
from src.workflow.service.create import create_workflow  # TODO: WorkflowManager will be implemented later

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="create", help="创建一个新的任务")
@click.option("-t", "--title", required=True, help="任务标题 (必需)")
@click.option("-d", "--desc", "--description", help="任务描述")
@click.option("-a", "--assignee", help="负责人")
@click.option("-l", "--label", multiple=True, help="标签 (可多次使用)")
@click.option("-s", "--status", default="open", help="初始状态 (默认: open)")
@click.option("--due", help="截止日期 (格式: YYYY-MM-DD，默认为创建日期后3天)")
@click.option("--link-roadmap", help="关联到 Roadmap Item (Story ID)")
@click.option("--link-workflow-stage", help="关联到 Workflow Stage Instance ID")
@click.option("--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")
@click.option("-f", "--flow", "--workflow", help="关联到工作流类型")
@click.option("-r", "--ref", "--reference", help="关联参考文档路径")
def create_task_command(
    title: str,
    desc: Optional[str],
    assignee: Optional[str],
    label: Optional[List[str]],
    status: str,
    due: Optional[str],
    link_roadmap: Optional[str],
    link_workflow_stage: Optional[str],
    link_github: Optional[str],
    flow: Optional[str],
    ref: Optional[str],
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
            due_date=due,
            link_roadmap_item_id=link_roadmap,
            link_workflow_stage_instance_id=link_workflow_stage,
            link_github_issue=link_github,
            flow=flow,
            ref_path=ref,
        )

        # 输出结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("task"):
                # 使用task_click模块中的format_output函数格式化输出
                from src.cli.commands.task.task_click import format_output

                print(format_output(result["task"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def create_task(
    title: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    status: Optional[str] = "open",
    due_date: Optional[str] = None,
    link_roadmap_item_id: Optional[str] = None,
    link_workflow_stage_instance_id: Optional[str] = None,
    link_github_issue: Optional[str] = None,
    flow: Optional[str] = None,
    ref_path: Optional[str] = None,
) -> Dict[str, Any]:
    """执行创建任务的核心逻辑"""
    logger.info(
        f"执行创建任务命令: title='{title}', assignee={assignee}, "
        f"labels={label}, status={status}, due_date={due_date}, "
        f"link_roadmap={link_roadmap_item_id}, "
        f"link_stage={link_workflow_stage_instance_id}, "
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
    }

    # 如果没有指定assignee，默认设置为"AI Agent"
    if not assignee:
        assignee = "AI Agent"
        logger.info(f"没有指定负责人，默认设置为: {assignee}")

    # 获取配置信息
    config = get_config()
    github_owner = config.get("github.owner", None)

    # 记录负责人信息
    logger.info(f"任务负责人: {github_owner or '未设置'}")

    task_data = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "labels": label,
        "status": status,
        "due_date": due_date,
        "roadmap_item_id": link_roadmap_item_id,
        "workflow_stage_instance_id": link_workflow_stage_instance_id,
    }

    # --- 解析并处理 GitHub 链接 ---
    github_issue_number = None
    if link_github_issue:
        try:
            # 解析GitHub链接
            if "#" not in link_github_issue or "/" not in link_github_issue.split("#")[0]:
                raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
            repo_part, issue_num_str = link_github_issue.split("#", 1)
            github_issue_number = int(issue_num_str)
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
        task_service = TaskService()
        session_factory = get_session_factory()
        with session_factory() as session:
            task_repo = TaskRepository(session)
            # 使用 create_task，传递单独的参数而非整个字典
            new_task = task_repo.create_task(
                title=task_data.get("title"),
                description=task_data.get("description"),
                status=task_data.get("status"),
                priority=task_data.get("priority", "medium"),
                assignee=task_data.get("assignee"),
                story_id=task_data.get("story_id"),
                labels=task_data.get("labels"),
                due_date=task_data.get("due_date"),
            )
            session.commit()  # 需要 commit 来持久化

            task_dict = new_task.to_dict()
            results["task"] = task_dict
            results["message"] = f"成功创建任务 (ID: {new_task.id})"

            # --- 控制台输出 ---
            console.print(f"[bold green]成功:[/bold green] 已创建任务 '{new_task.title}' (ID: {new_task.id})")

            # 创建任务日志
            create_task_log(new_task.id, new_task.title, description, assignee, ref_path)

            # 如果指定了参考文档，存储到Memory并关联
            if ref_path:
                try:
                    logger.info(f"尝试存储参考文档到Memory: {ref_path}")
                    memory_result = store_ref_to_memory(new_task.id, ref_path)
                    if not memory_result["success"]:
                        error_msg = memory_result.get("error", "未知错误")
                        logger.warning(f"存储参考文档到Memory失败: {error_msg}")
                        console.print(f"[bold yellow]警告:[/bold yellow] 存储参考文档到Memory失败: {error_msg}")
                        # 添加到结果中，但不影响任务创建的成功状态
                        if "warnings" not in results:
                            results["warnings"] = []
                        results["warnings"].append(f"参考文档存储失败: {error_msg}")
                except Exception as e:
                    logger.error(f"存储参考文档到Memory时出错: {str(e)}", exc_info=True)
                    console.print(f"[bold yellow]警告:[/bold yellow] 存储参考文档到Memory时出错: {str(e)}")
                    if "warnings" not in results:
                        results["warnings"] = []
                    results["warnings"].append(f"参考文档存储出错: {str(e)}")

            # 如果指定了工作流类型，创建并关联工作流会话
            if flow:
                try:
                    logger.info(f"尝试关联任务 {new_task.id} 到工作流 '{flow}'")
                    # 通过工作流ID或名称关联工作流会话
                    session = task_service.link_to_flow_session(new_task.id, flow_type=flow)
                    if session:
                        logger.info(f"成功关联到工作流会话 '{session.get('name')}' (ID: {session.get('id')})")
                        console.print(f"[bold green]成功:[/bold green] 已关联到工作流会话 '{session.get('name')}' (ID: {session.get('id')})")
                        # 将会话信息添加到结果中
                        results["workflow_session"] = session

                        # 记录到任务日志
                        append_to_task_log(new_task.id, f"关联到工作流: {flow}", {"session_id": session.get("id"), "session_name": session.get("name")})
                except ValueError as ve:
                    # 详细记录错误原因
                    error_message = str(ve)
                    logger.warning(f"关联工作流失败: {error_message}")
                    console.print(f"[bold yellow]警告:[/bold yellow] 创建任务成功，但关联工作流失败: {error_message}")
                    # 不影响任务创建本身，只是记录警告
                    results["message"] += f"，但关联工作流失败: {error_message}"
                    results["warnings"] = [f"关联工作流失败: {error_message}"]

                    # 记录到任务日志
                    append_to_task_log(new_task.id, f"关联工作流失败", {"error": error_message, "flow": flow})
                except Exception as e:
                    # 处理其他可能的异常
                    error_message = f"关联工作流时发生意外错误: {str(e)}"
                    logger.error(error_message, exc_info=True)
                    console.print(f"[bold yellow]警告:[/bold yellow] 创建任务成功，但关联工作流失败: {error_message}")
                    results["message"] += f"，但关联工作流失败: {error_message}"
                    results["warnings"] = [error_message]

                    # 记录到任务日志
                    append_to_task_log(new_task.id, f"关联工作流失败", {"error": error_message, "flow": flow})

            # 设置为当前任务
            task_service.set_current_task(new_task.id)

            # 记录到任务日志
            append_to_task_log(new_task.id, "设置为当前任务")

    except ValueError as ve:  # 处理 Repository 中可能的 JSON 字段验证错误
        logger.error(f"创建任务时数据验证失败: {ve}", exc_info=True)
        results["status"] = "error"
        results["code"] = 400
        results["message"] = f"创建任务失败: {ve}"
        console.print(f"[bold red]错误:[/bold red] {ve}")
    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"创建任务时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results


def create_task_log(
    task_id: str,
    title: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    ref_path: Optional[str] = None,
) -> None:
    """创建任务日志文件"""
    # 创建目录结构
    config = get_config()
    agent_work_dir = config.get("paths.agent_work_dir", ".ai")
    task_dir = os.path.join(agent_work_dir, "tasks", task_id)
    os.makedirs(task_dir, exist_ok=True)

    # 创建日志文件
    log_path = os.path.join(task_dir, "task.log")

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "w") as f:
        f.write(f"# 任务日志: {title} (ID: {task_id})\n\n")
        f.write(f"## {current_time} - 任务创建\n")
        f.write(f"- 标题: {title}\n")
        if description:
            f.write(f"- 描述: {description}\n")
        if assignee:
            f.write(f"- 负责人: {assignee}\n")
        if ref_path:
            f.write(f"- 参考文档: {ref_path}\n")
        f.write("\n")


def _get_default_task_name(task_title: Optional[str] = None) -> str:
    # ... (省略)
    return "未命名任务"


def _create_task_metadata_file(task_dir: str, task_id: str, task_data: Dict[str, Any]):
    # ... (省略)
    pass


def _create_task_structure(task_id: str, task_data: Dict[str, Any]) -> Optional[str]:
    """创建任务所需的文件结构"""
    config = get_config()
    project_root = config.get("paths.project_root", os.getcwd())
    agent_work_dir = config.get("paths.agent_work_dir", ".ai")  # 从配置获取 Agent 工作目录

    # 使用 agent_work_dir 构建路径
    task_dir = os.path.join(project_root, agent_work_dir, "tasks", task_id)
    ensure_directory_exists(task_dir)

    # 创建元数据文件等逻辑...
    metadata_path = os.path.join(task_dir, "metadata.json")
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        click.echo(f"错误: 无法写入任务元数据文件 {metadata_path}: {e}", err=True)
        return None

    # 可能还需要创建其他文件或子目录，例如日志目录
    log_dir = os.path.join(task_dir, "logs")
    ensure_directory_exists(log_dir)

    # 创建一个空的 task.log 文件，如果需要的话
    log_file_path = os.path.join(task_dir, "task.log")
    try:
        Path(log_file_path).touch(exist_ok=True)
    except IOError as e:
        click.echo(f"警告: 无法创建任务日志文件 {log_file_path}: {e}", err=True)

    return task_dir
