"""
任务日志显示工具模块
"""

import logging
from typing import Any, Dict

import yaml
from rich.console import Console

from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


def show_task_log(task_id: str, task_title: str) -> Dict[str, Any]:
    """显示任务日志

    Args:
        task_id: 任务ID
        task_title: 任务标题

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
        # 获取任务服务实例
        task_service = TaskService()

        # 获取日志路径和内容
        log_path, log_dir = task_service.get_task_log_path(task_id)
        log_content = task_service.read_task_log(task_id)

        if log_content is not None:
            # 构建日志信息字典
            log_info = {"任务ID": task_id, "任务标题": task_title, "日志目录": log_dir, "日志内容": log_content}

            # 输出日志信息
            console.print(yaml.dump(log_info, allow_unicode=True, sort_keys=False))
            results["data"] = log_info
            results["message"] = "成功读取任务日志"
        else:
            console.print("\n[bold yellow]未找到任务日志[/bold yellow]")
            console.print(f"预期路径: {log_path}")
            results["status"] = "warning"
            results["message"] = "未找到任务日志"

    except Exception as e:
        logger.error(f"读取任务日志时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"读取任务日志时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
