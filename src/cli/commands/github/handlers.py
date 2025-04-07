"""
GitHub 命令处理器

处理 GitHub 相关命令
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def handle_github_command(args: List[str]) -> Dict[str, Any]:
    """处理 GitHub 命令

    Args:
        args: 命令参数列表

    Returns:
        Dict[str, Any]: 命令执行结果
    """
    try:
        # 解析参数
        action = None
        command_type = None
        task_id = None
        status = None
        sync = False
        milestone = None
        direction = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                param = arg[2:]
                if "=" in param:
                    key, value = param.split("=", 1)
                    if key == "action":
                        action = value
                    elif key == "type":
                        command_type = value
                    elif key == "id":
                        task_id = value
                    elif key == "status":
                        status = value
                    elif key == "sync":
                        sync = value.lower() == "true"
                    elif key == "milestone":
                        milestone = value
                    elif key == "direction":
                        direction = value
            i += 1

        # 根据动作执行相应操作
        if action == "check":
            if command_type == "roadmap":
                return {"success": True, "message": "检查路线图", "data": {"type": command_type}}
            else:
                return {"success": False, "error": f"不支持的检查类型: {command_type}"}
        elif action == "update":
            if command_type == "task" and task_id and status:
                return {
                    "success": True,
                    "message": f"更新任务 {task_id} 状态为 {status}",
                    "data": {"type": command_type, "id": task_id, "status": status, "sync": sync},
                }
            else:
                return {"success": False, "error": "更新任务需要指定任务ID和状态"}
        elif action == "list":
            if command_type == "task" and milestone:
                return {
                    "success": True,
                    "message": f"列出里程碑 {milestone} 的任务",
                    "data": {"type": command_type, "milestone": milestone},
                }
            else:
                return {"success": False, "error": "列出任务需要指定里程碑"}
        elif action == "sync":
            if direction:
                return {
                    "success": True,
                    "message": f"同步方向: {direction}",
                    "data": {"direction": direction},
                }
            else:
                return {"success": False, "error": "同步需要指定方向"}
        else:
            return {"success": False, "error": f"未知的操作: {action}"}

    except Exception as e:
        logger.error(f"处理 GitHub 命令失败: {str(e)}")
        return {"success": False, "error": f"处理命令失败: {str(e)}"}
