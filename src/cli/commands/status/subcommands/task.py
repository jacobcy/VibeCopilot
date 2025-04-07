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

        # 检查是否存在错误
        if "error" in result:
            print(f"错误: {result['error']}")

            # 显示错误代码
            if "code" in result:
                print(f"错误代码: {result['code']}")

            # 显示自定义建议
            if "suggestions" in result and isinstance(result["suggestions"], list):
                print("\n修复建议:")
                for suggestion in result["suggestions"]:
                    print(f"  - {suggestion}")
                return 1
            else:
                # 使用通用建议
                print("\n通用建议:")
                print("  - 检查任务健康状态并解决问题")
                print("  - 查看日志获取详细错误信息")
                return 1

        output_result(result, output_format, "domain", verbose)
        return 0
    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}", exc_info=True)
        print(f"错误: {str(e)}")
        return 1
