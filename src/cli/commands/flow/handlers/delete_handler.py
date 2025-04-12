"""
Flow 'delete' subcommand handler.
"""
import logging
import os
from typing import Any, Dict

from rich.console import Console
from rich.prompt import Confirm

from src.workflow.search.workflow_search import get_workflow_fuzzy
from src.workflow.workflow_operations import delete_workflow, get_workflow, get_workflows_directory

logger = logging.getLogger(__name__)
console = Console()


def handle_delete_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理删除工作流子命令

    Args:
        args: 命令参数，包括：
            - workflow_id: 要删除的工作流ID
            - force: 是否强制删除，不提示确认
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow delete", "args": args},
    }

    try:
        # 获取参数
        workflow_id = args.get("workflow_id")
        force = args.get("force", False)
        verbose = args.get("verbose", False)

        if not workflow_id:
            result["message"] = "缺少必要参数: workflow_id"
            result["code"] = 400
            return result

        # 尝试找到工作流
        workflow_dir = get_workflows_directory()
        workflow = get_workflow_fuzzy(workflow_id)

        if not workflow:
            result["message"] = f"未找到ID或名称为 '{workflow_id}' 的工作流"
            result["code"] = 404
            return result

        # 获取实际的工作流ID
        actual_id = workflow.get("id")
        workflow_name = workflow.get("name", "未命名工作流")

        if verbose:
            console.print(f"找到工作流: [bold]{workflow_name}[/bold] (ID: {actual_id})")

        # 确认删除，除非使用了--force
        confirmed = force
        if not force and not args.get("_agent_mode", False):
            confirmed = Confirm.ask(f"确定要删除工作流 [bold]{workflow_name}[/bold] (ID: {actual_id})?")

        if not confirmed:
            result["status"] = "cancelled"
            result["code"] = 0
            result["message"] = "删除操作已取消"
            return result

        # 执行删除
        if delete_workflow(actual_id, workflow_dir):
            result["status"] = "success"
            result["code"] = 0
            result["message"] = f"成功删除工作流: {workflow_name} (ID: {actual_id})"
            result["data"] = {"id": actual_id, "name": workflow_name}
        else:
            result["message"] = f"删除工作流失败: {actual_id}"
            result["code"] = 500

        return result

    except Exception as e:
        logger.error(f"删除工作流时出错: {str(e)}", exc_info=True)
        result["message"] = f"删除工作流时出错: {str(e)}"
        result["code"] = 500
        return result
