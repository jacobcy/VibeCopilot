"""
状态init子命令

处理初始化项目状态的子命令
"""

import logging
from typing import Any, Dict

from src.cli.commands.status.output_helpers import output_result
from src.status import StatusService

logger = logging.getLogger(__name__)


def handle_init(service: StatusService, args: Dict[str, Any]) -> int:
    """处理init子命令

    Args:
        service: 状态服务实例
        args: 命令参数

    Returns:
        命令状态码，0表示成功
    """
    project_name = args.get("name")
    output_format = args.get("format", "text")

    try:
        result = service.initialize_project_status(project_name)

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
                print("  - 确保项目名称有效")
                print("  - 检查是否已经初始化过项目")
                return 1

        print(f"✅ 初始化成功: 项目 '{result.get('name', 'VibeCopilot')}' 已初始化")
        output_result(result, output_format, "system", True)
        return 0
    except Exception as e:
        logger.error(f"初始化项目状态时出错: {str(e)}", exc_info=True)
        print(f"错误: {str(e)}")
        return 1
