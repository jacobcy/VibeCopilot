"""
Flow 'list' subcommand handler.
"""
import argparse
import logging
from typing import Any, Dict

# Assuming these helpers are still needed and accessible
# Adjust path if they were moved
from src.workflow.flow_cmd.helpers import format_workflow_stages
from src.workflow.workflow_operations import list_workflows

logger = logging.getLogger(__name__)


def handle_list_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理列表子命令

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
        "meta": {"command": "flow list", "args": args},
    }

    try:
        # 获取参数
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        # 转换为 argparse.Namespace 对象
        args_namespace = argparse.Namespace()
        args_namespace.verbose = verbose
        args_namespace.format = output_format
        args_namespace.no_print = args.get("_agent_mode", False)

        # 获取工作流列表
        result_dict = list_workflows(args_namespace)  # Pass the args_namespace to list_workflows

        # 检查 list_workflows 的返回值
        if not isinstance(result_dict, dict) or "workflows" not in result_dict:
            logger.error(f"list_workflows 返回了意外的格式: {result_dict}")
            result["message"] = "获取工作流列表时内部错误"
            result["code"] = 500
            return result

        # 提取工作流列表
        workflow_data = result_dict.get("workflows", [])

        if not workflow_data:
            result["status"] = "success"
            result["code"] = 0
            result["message"] = "没有找到工作流定义"
            result["data"] = {"workflows": []}
            return result

        # Prepare data structure - workflow_data is already a list of dicts
        # workflow_data = [wf for wf in workflows]

        result["status"] = "success"
        result["code"] = 0
        result["message"] = f"共找到 {len(workflow_data)} 个工作流定义"
        result["data"] = {"workflows": workflow_data}

        # Format for console output if not agent mode and format is text
        if output_format == "text" and not args.get("_agent_mode", False):
            # 文本格式处理
            output_lines = []
            for workflow in workflow_data:
                # 确保 workflow 是字典
                if isinstance(workflow, dict):
                    info = f"{workflow.get('id', 'N/A')}: {workflow.get('name', 'Unnamed')}"
                    if verbose:
                        description = workflow.get("description", "无描述")
                        info += f"\n  描述: {description}"
                        stages = workflow.get("stages", [])
                        if stages:
                            # Assuming format_workflow_stages takes list of stage dicts
                            stages_info = format_workflow_stages(stages)
                            info += f"\n  阶段: {stages_info}"
                    output_lines.append(info)
                else:
                    logger.warning(f"工作流数据格式不正确: {workflow}")

            # Override message with formatted text for direct console display
            result["message"] = f"共找到 {len(workflow_data)} 个工作流定义:\n" + "\n".join(output_lines)

        return result

    except Exception as e:
        logger.error(f"获取工作流列表时出错: {str(e)}", exc_info=True)
        result["message"] = f"获取工作流列表时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
