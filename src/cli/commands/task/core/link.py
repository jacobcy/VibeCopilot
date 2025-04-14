"""
任务关联工作流命令模块
"""

import logging
from typing import Any, Dict, Optional

import click
from loguru import logger
from rich.console import Console

from src.services.task import TaskService

logger = logging.getLogger(__name__)
console = Console()


def is_agent_mode() -> bool:
    """检查是否处于 Agent 模式"""
    return False


@click.command(name="link", help="关联任务到工作流会话")
@click.argument("task_id", type=str, required=False)
@click.option("-f", "--flow", type=str, help="工作流ID或名称")
@click.option("-s", "--session", type=str, help="会话ID")
def link_task(task_id: Optional[str] = None, flow: Optional[str] = None, session: Optional[str] = None):
    """关联任务到工作流会话命令

    将任务关联到工作流会话，支持创建新会话或关联到已有会话。

    示例:
        vibecopilot task link abc123 --flow dev   # 创建开发工作流会话并关联
        vibecopilot task link --flow 测试工作流   # 使用当前任务创建测试工作流会话
        vibecopilot task link --session sess_id   # 关联当前任务到指定会话
    """
    try:
        # 执行关联任务到工作流的逻辑
        result = execute_link_flow_task(task_id, flow, session)

        # 显示结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")

            # 显示会话信息
            if result.get("session"):
                session_info = result["session"]
                console.print(f"会话ID: {session_info.get('id')}")
                console.print(f"会话名称: {session_info.get('name')}")
                console.print(f"工作流: {session_info.get('workflow_id')}")
                console.print(f"工作流类型: {session_info.get('flow_type')}")
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")

        return result
    except Exception as e:
        logger.error(f"执行关联任务到工作流命令时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return {"status": "error", "message": str(e)}


def execute_link_flow_task(task_id: Optional[str] = None, flow: Optional[str] = None, session: Optional[str] = None) -> Dict[str, Any]:
    """关联任务到工作流会话的核心逻辑"""
    try:
        task_service = TaskService()

        # 如果没有指定任务ID，使用当前任务
        if not task_id:
            current_task = task_service.get_current_task()
            if not current_task:
                return {"status": "error", "message": "没有指定任务ID且没有当前任务"}
            task_id = current_task["id"]

        # 验证参数
        if not flow and not session:
            return {"status": "error", "message": "必须指定工作流(--flow)或会话ID(--session)"}
        if flow and session:
            return {"status": "error", "message": "不能同时指定工作流和会话ID"}

        # 关联到工作流会话
        try:
            result = task_service.link_to_flow_session(task_id, flow_type=flow, session_id=session)
            return {"status": "success", "message": "任务关联成功", "session": result}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    except Exception as e:
        logger.error(f"关联任务失败: {e}")
        return {"status": "error", "message": f"关联任务失败: {str(e)}"}
