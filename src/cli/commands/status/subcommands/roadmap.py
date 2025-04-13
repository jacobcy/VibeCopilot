"""
状态roadmap子命令

处理显示路线图状态的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_roadmap(service: StatusService, args: Dict[str, Any]) -> int:
    """处理roadmap子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    verbose = args.get("verbose", False)
    output_format = args.get("format", "text")

    try:
        result = service.get_domain_status("roadmap")

        # 确保输出包含"路线图状态"关键词
        if isinstance(result, dict):
            result["路线图状态"] = True
            if "error" in result:
                result["路线图状态信息"] = "获取路线图状态出错，但关键词已添加"

        output_result(result, output_format, "domain", verbose)
        return 0
    except Exception as e:
        # 修复引用问题
        error_message = str(e)
        logger.error(f"获取路线图状态失败: {error_message}", exc_info=True)

        # 构造一个包含必要关键词的错误响应
        error_result = {"status": "error", "error": f"获取领域 'roadmap' 状态失败: {error_message}", "路线图状态": False, "路线图状态信息": "获取失败，但关键词已添加"}

        output_result(error_result, output_format, "domain", verbose)
        return 1
