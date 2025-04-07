"""
Flow 'start' subcommand handler.
"""
import logging
from typing import Any, Dict

# Assuming workflow_operations and run_handler are accessible
from src.workflow.workflow_operations import get_workflow_by_type

# Uses the run subcommand handler internally
from .run_handler import handle_run_subcommand

logger = logging.getLogger(__name__)


def handle_start_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理启动子命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    # 启动命令实际上是run命令的特殊情况，它找到定义并运行第一个阶段
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow start", "args": args},
    }

    try:
        # 获取参数
        workflow_type = args.get("workflow_type")  # The definition identifier
        name = args.get("name")  # Optional name for the new session
        context_data = args.get("context_data", {})  # Pass initial context
        roadmap_item_id = args.get("roadmap_item_id")  # Link to Story/Epic

        # 检查参数
        if not workflow_type:
            result["message"] = "必须提供工作流类型/定义ID"
            result["code"] = 400
            return result

        # 获取工作流定义 (Adjust based on how definitions are stored/retrieved)
        # Assume get_workflow_by_type retrieves the definition structure
        workflow_def = get_workflow_by_type(workflow_type)
        if not workflow_def:
            result["message"] = f"找不到工作流定义: {workflow_type}"
            result["code"] = 404
            return result

        # 获取第一个阶段
        stages = workflow_def.get("stages", [])
        if not stages:
            result["message"] = f"工作流 '{workflow_type}' 没有定义阶段"
            result["code"] = 400
            return result

        first_stage = stages[0]
        stage_id = first_stage.get("id")
        if not stage_id:
            result["message"] = f"工作流 '{workflow_type}' 的第一个阶段缺少ID"
            result["code"] = 500
            return result

        # 构建run命令的参数
        run_args = {
            "workflow_id": workflow_type,  # Pass definition ID
            "stage": stage_id,  # Target the first stage
            "name": name or f"{workflow_type}_session_{roadmap_item_id or 'new'}",  # Generate a name if not provided
            "session": None,  # Explicitly None to indicate starting a new session
            "completed": [],  # Start with no completed items
            "context_data": context_data,  # Pass any initial context
            "roadmap_item_id": roadmap_item_id,  # Pass roadmap link
            "_agent_mode": args.get("_agent_mode", False),  # Preserve agent mode flag
        }

        # 调用run命令处理器
        logger.info(f"启动新工作流 '{workflow_type}' (调用 run handler)...")
        run_result = handle_run_subcommand(run_args)

        # Modify metadata to reflect 'start' command origin
        if isinstance(run_result.get("meta"), dict):
            run_result["meta"]["original_command"] = "flow start"
        else:
            run_result["meta"] = {
                "original_command": "flow start",
                "args": args,
            }  # Ensure meta exists

        return run_result

    except Exception as e:
        logger.error(f"启动工作流时出错: {str(e)}", exc_info=True)
        result["message"] = f"启动工作流时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
