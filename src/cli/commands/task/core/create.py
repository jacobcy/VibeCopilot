# src/cli/commands/task/core/create.py

import logging
from typing import Any, Dict, List, Optional

import click
from loguru import logger
from rich.console import Console

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.services.task import TaskService

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="create", help="创建一个新的任务")
@click.option("-t", "--title", required=True, help="任务标题 (必需)")
@click.option("-d", "--desc", help="任务描述")
@click.option("-a", "--assignee", help="负责人")
@click.option("-l", "--label", multiple=True, help="标签 (可多次使用)")
@click.option("-s", "--status", default="open", help="初始状态 (默认: open)")
@click.option("--link-roadmap", help="关联到 Roadmap Item (Story ID)")
@click.option("--link-workflow-stage", help="关联到 Workflow Stage Instance ID")
@click.option("--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")
@click.option("--flow", help="关联到工作流类型")
def create_task(title, desc, assignee, label, status, link_roadmap, link_workflow_stage, link_github, flow):
    """创建一个新的任务

    创建一个新的任务，支持设置标题、描述、负责人、标签等基本信息，
    以及关联到 Roadmap Item、Workflow Stage 或 GitHub Issue。
    """
    try:
        # 执行创建任务的逻辑
        result = execute_create_task(
            title=title,
            description=desc,
            assignee=assignee,
            label=list(label) if label else None,
            status=status,
            link_roadmap_item_id=link_roadmap,
            link_workflow_stage_instance_id=link_workflow_stage,
            link_github_issue=link_github,
            flow=flow,
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


def execute_create_task(
    title: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    status: Optional[str] = "open",
    link_roadmap_item_id: Optional[str] = None,
    link_workflow_stage_instance_id: Optional[str] = None,
    link_github_issue: Optional[str] = None,
    flow: Optional[str] = None,
) -> Dict[str, Any]:
    """执行创建任务的核心逻辑"""
    logger.info(
        f"执行创建任务命令: title='{title}', assignee={assignee}, "
        f"labels={label}, status={status}, "
        f"link_roadmap={link_roadmap_item_id}, "
        f"link_stage={link_workflow_stage_instance_id}, "
        f"link_github={link_github_issue}, flow={flow}"
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

    task_data = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "labels": label,
        "status": status,
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
            # 使用 create_task 来处理 JSON 字段
            new_task = task_repo.create_task(task_data)
            session.commit()  # 需要 commit 来持久化

            task_dict = new_task.to_dict()
            results["task"] = task_dict
            results["message"] = f"成功创建任务 (ID: {new_task.id})"

            # --- 控制台输出 ---
            console.print(f"[bold green]成功:[/bold green] 已创建任务 '{new_task.title}' (ID: {new_task.id})")

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
                except ValueError as ve:
                    # 详细记录错误原因
                    error_message = str(ve)
                    logger.warning(f"关联工作流失败: {error_message}")
                    console.print(f"[bold yellow]警告:[/bold yellow] 创建任务成功，但关联工作流失败: {error_message}")
                    # 不影响任务创建本身，只是记录警告
                    results["message"] += f"，但关联工作流失败: {error_message}"
                    results["warnings"] = [f"关联工作流失败: {error_message}"]
                except Exception as e:
                    # 处理其他可能的异常
                    error_message = f"关联工作流时发生意外错误: {str(e)}"
                    logger.error(error_message, exc_info=True)
                    console.print(f"[bold yellow]警告:[/bold yellow] 创建任务成功，但关联工作流失败: {error_message}")
                    results["message"] += f"，但关联工作流失败: {error_message}"
                    results["warnings"] = [error_message]

            # 设置为当前任务
            task_service.set_current_task(new_task.id)

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
