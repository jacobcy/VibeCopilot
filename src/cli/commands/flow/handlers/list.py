"""
Flow 'list' subcommand handler.
"""

import logging
from typing import Any, Dict

from src.cli.commands.flow.handlers.formatter import format_workflow_summary

# Assuming these helpers are still needed and accessible
# 使用flow_cmd模块中的功能替代operations
from src.workflow.utils.helpers import format_workflow_stages
from src.workflow.utils.workflow_search import list_workflows

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

        # 获取工作流列表
        workflows = list_workflows()  # 返回的是一个工作流列表

        # 如果没有找到工作流
        if not workflows:
            result["status"] = "success"
            result["code"] = 0
            result["message"] = "没有找到工作流定义"
            result["data"] = {"workflows": []}
            return result

        result["status"] = "success"
        result["code"] = 0
        result["message"] = f"共找到 {len(workflows)} 个工作流定义"
        result["data"] = {"workflows": workflows}

        # Format for console output if not agent mode and format is text
        if output_format == "text" and not args.get("_agent_mode", False):
            # 文本格式处理
            output_lines = []
            for workflow in workflows:
                # 确保 workflow 是字典
                if isinstance(workflow, dict):
                    # 使用format_workflow_summary保持一致的格式
                    workflow_summary = format_workflow_summary(workflow)
                    output_lines.append(workflow_summary)

                    if verbose:
                        # 添加额外的详细信息
                        stages = workflow.get("stages", [])
                        if stages:
                            # Assuming format_workflow_stages takes list of stage dicts
                            stages_info = format_workflow_stages(stages)
                            output_lines.append(f"  阶段: {stages_info}")
                        output_lines.append("")
                else:
                    logger.warning(f"工作流数据格式不正确: {workflow}")

            # Override message with formatted text for direct console display
            result["message"] = f"共找到 {len(workflows)} 个工作流定义:\n" + "\n".join(output_lines)

        return result

    except Exception as e:
        logger.error(f"获取工作流列表时出错: {str(e)}", exc_info=True)
        result["message"] = f"获取工作流列表时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
