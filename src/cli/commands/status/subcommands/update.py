"""
状态update子命令

处理更新项目阶段的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_update(service: StatusService, args: Dict[str, Any]) -> int:
    """处理update子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    phase = args.get("phase")
    output_format = args.get("format", "text")

    if not phase:
        logger.error("缺少必要参数: --phase")
        print("错误: 缺少必要参数: --phase")
        return 1

    try:
        result = service.update_project_phase(phase)

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
                print("  - 确保项目阶段名称正确")
                print("  - 检查是否有权限更新项目阶段")
                return 1

        output_result(result, output_format, "system", True)
        return 0
    except Exception as e:
        logger.error(f"更新项目阶段时出错: {str(e)}", exc_info=True)
        print(f"错误: {str(e)}")
        return 1
