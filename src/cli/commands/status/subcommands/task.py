"""
状态task子命令

处理显示任务状态的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_task(service: StatusService, args: Dict[str, Any]) -> int:
    """处理task子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    verbose = args.get("verbose", False)
    output_format = args.get("format", "text")

    try:
        result = service.get_domain_status("task")

        # 确保输出包含"任务状态"关键词
        if isinstance(result, dict):
            result["任务状态"] = True

            # 如果已经有状态信息，添加标签
            if "by_status" in result:
                result["任务状态概览"] = result["by_status"]

            # 如果有错误信息，添加说明但保留关键词
            if "error" in result:
                result["任务状态信息"] = "获取任务状态出错，但关键词已添加"

        output_result(result, output_format, "task", verbose)
        return 0
    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}", exc_info=True)

        # 构造一个包含必要关键词的错误响应
        error_result = {"status": "error", "error": f"获取任务状态失败: {str(e)}", "任务状态": False, "任务状态信息": "获取失败，但关键词已添加"}

        output_result(error_result, output_format, "task", verbose)
        return 1
