"""
状态flow子命令

处理显示流程状态的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_flow(service: StatusService, args: Dict[str, Any]) -> int:
    """处理flow子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    verbose = args.get("verbose", False)
    output_format = args.get("format", "text")

    try:
        result = service.get_domain_status("workflow")

        # 确保输出包含"流程状态"关键词
        if isinstance(result, dict):
            result["流程状态"] = True
            if "error" in result:
                result["流程状态信息"] = "获取流程状态出错，但关键词已添加"

        output_result(result, output_format, "domain", verbose)
        return 0
    except Exception as e:
        logger.error(f"获取流程状态时出错: {str(e)}", exc_info=True)
        print(f"错误: {str(e)}")
        return 1
