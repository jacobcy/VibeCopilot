"""
Flow 'run' subcommand handler.
"""
import logging
from typing import Any, Dict

# Assuming workflow_runner is accessible
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage

logger = logging.getLogger(__name__)


def handle_run_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理运行子命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow run", "args": args},
    }

    try:
        # 获取参数
        workflow_id = args.get("workflow_id")  # Should this be definition ID?
        stage_id = args.get("stage")
        instance_name = args.get("name")
        session_id = args.get("session")  # Crucial for continuing a session
        completed_items = args.get("completed", [])  # Input for checklist progress
        context_data = args.get("context_data", {})  # Optional additional context

        # 检查参数 - session_id is likely the most important identifier here
        if not session_id:
            # If no session ID, maybe workflow_id refers to definition to START a new session?
            # Requires clarification on how `flow run` is intended vs `flow start`
            if not workflow_id:
                result["message"] = "必须提供工作流定义ID或现有会话ID (session)"
                result["code"] = 400
                return result
            # If workflow_id is given but no session, maybe implies starting?
            # Let run_workflow_stage handle this logic for now.

        # Stage ID is required to know which stage to run/advance to
        if not stage_id:
            result["message"] = "必须提供目标阶段ID (stage)"
            result["code"] = 400
            return result

        # 运行工作流阶段
        # run_workflow_stage needs to handle finding/creating sessions and instances
        success, message, data = run_workflow_stage(
            workflow_id=workflow_id,  # Pass definition ID if starting new?
            stage_id=stage_id,
            instance_name=instance_name,  # Used if creating new session
            completed_items=completed_items,
            session_id=session_id,  # Pass existing session ID
            context_data=context_data,
        )

        if success:
            result["status"] = "success"
            result["code"] = 0
            result["message"] = message
            result["data"] = data
        else:
            result["message"] = message  # Error message from runner
            # Try to determine appropriate error code (e.g., 404 if not found, 500 for internal)
            result["code"] = data.get("error_code", 500) if isinstance(data, dict) else 500
            result["data"] = data  # Include any error details from runner

        return result

    except Exception as e:
        logger.error(f"运行工作流时出错: {str(e)}", exc_info=True)
        result["message"] = f"运行工作流时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
