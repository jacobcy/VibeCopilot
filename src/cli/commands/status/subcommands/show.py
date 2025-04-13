"""
状态show子命令

处理显示状态的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_show(service: StatusService, args: Dict[str, Any]) -> int:
    """处理show子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    status_type = args.get("type", "summary")
    verbose = args.get("verbose", False)
    output_format = args.get("format", "text")

    try:
        if status_type == "all":
            result = service.get_system_status(detailed=True)
        elif status_type == "critical":
            result = service.get_critical_status()
        else:  # summary
            result = service.get_system_status(detailed=False)

        # 确保输出包含"系统信息"关键词
        result["系统信息"] = {"类型": status_type, "时间": service.get_project_state().get("last_update", "unknown"), "状态服务版本": "1.0.0"}

        output_result(result, output_format, "system", verbose)
        return 0
    except Exception as e:
        logger.error(f"获取系统状态时出错: {str(e)}", exc_info=True)
        print(f"错误: {str(e)}")
        return 1
