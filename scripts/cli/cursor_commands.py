"""
Cursor命令处理模块

处理Cursor IDE中的命令解析和执行。
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .commands import process_command

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CursorCommandProcessor:
    """Cursor命令处理器"""

    def __init__(self) -> None:
        """初始化命令处理器"""
        # 命令格式: /command --arg1=value1 --arg2="value with spaces" arg3
        self.command_pattern = r"^/([a-zA-Z0-9_]+)\s*(.*)?$"
        self.args_pattern = r"--([a-zA-Z0-9_-]+)(?:=([^\s\"]+|\"[^\"]*\"))|\s+([^\s\"]+|\"[^\"]*\")"

    def parse_command(self, text: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        解析命令文本

        Args:
            text: 命令文本

        Returns:
            Tuple[Optional[str], Dict[str, Any]]: (命令名称, 参数字典)
        """
        # 检查是否是命令
        command_match = re.match(self.command_pattern, text.strip())
        if not command_match:
            return None, {}

        # 提取命令名称和参数部分
        command_name = command_match.group(1)
        args_text = command_match.group(2) or ""

        # 解析参数
        args = {}
        positional_args = []

        # 查找所有命名参数 (--arg=value 或 --arg="value with spaces")
        for arg_match in re.finditer(r"--([a-zA-Z0-9_-]+)(?:=([^\s\"]+|\"[^\"]*\"))?", args_text):
            arg_name = arg_match.group(1)
            arg_value = arg_match.group(2) or True  # 如果只有--arg，则值为True

            # 如果值是带引号的，去掉引号
            if isinstance(arg_value, str) and arg_value.startswith('"') and arg_value.endswith('"'):
                arg_value = arg_value[1:-1]

            args[arg_name] = arg_value

        # 剩余部分作为位置参数
        # 替换掉所有已识别的命名参数
        remaining_text = re.sub(
            r"--[a-zA-Z0-9_-]+(?:=[^\s\"]+|=\"[^\"]*\")?", "", args_text
        ).strip()

        # 分割位置参数，保留引号中的空格
        if remaining_text:
            parts = []
            in_quote = False
            current_part = ""

            for char in remaining_text:
                if char == '"' and not in_quote:
                    in_quote = True
                elif char == '"' and in_quote:
                    in_quote = False
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                elif char == " " and not in_quote:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                else:
                    current_part += char

            if current_part:
                parts.append(current_part)

            positional_args = parts

        # 将位置参数添加到参数字典
        if positional_args:
            args["_positional"] = positional_args

        return command_name, args

    def execute_command(self, text: str) -> Dict[str, Any]:
        """
        执行命令

        Args:
            text: 命令文本

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 解析命令
        command_name, args = self.parse_command(text)

        # 如果不是命令
        if not command_name:
            return {"success": False, "error": "不是有效的命令"}

        # 调用命令处理函数
        try:
            result = process_command(command_name, args)
            return result
        except Exception as e:
            logger.exception(f"执行命令 {command_name} 失败")
            return {"success": False, "error": f"执行命令失败: {str(e)}"}


# 创建命令处理器实例
cursor_cmd_processor = CursorCommandProcessor()


def handle_cursor_command(text: str) -> Dict[str, Any]:
    """
    处理Cursor命令的全局函数

    Args:
        text: 命令文本

    Returns:
        Dict[str, Any]: 命令执行结果
    """
    return cursor_cmd_processor.execute_command(text)


def main():
    """命令行入口点"""
    import sys

    if len(sys.argv) < 2:
        print("错误: 请提供命令文本")
        sys.exit(1)

    # 获取命令文本
    command_text = sys.argv[1]

    # 处理命令
    result = handle_cursor_command(command_text)

    # 输出结果
    if result.get("success"):
        if "message" in result:
            print(result["message"])
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"错误: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
