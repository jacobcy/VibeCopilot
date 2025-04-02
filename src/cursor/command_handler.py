"""
Cursor命令处理器

处理Cursor中的命令并调用相应的处理函数。
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from src.cli.cursor_commands import handle_cursor_command

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 命令处理函数类型
CommandHandlerType = Callable[[str], Dict[str, Any]]

# 注册的命令处理函数
_command_handlers: List[CommandHandlerType] = [handle_cursor_command]


def register_command_handler(handler: CommandHandlerType) -> None:
    """
    注册命令处理函数

    Args:
        handler: 命令处理函数
    """
    if handler not in _command_handlers:
        _command_handlers.append(handler)
        logger.info(f"注册命令处理函数: {handler.__name__}")


def handle_commands(text: str) -> Dict[str, Any]:
    """
    处理命令文本

    Args:
        text: 命令文本

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 检查是否是命令（以/开头）
    if not text.strip().startswith("/"):
        return {"success": False, "error": "不是命令"}

    # 尝试各个处理函数
    for handler in _command_handlers:
        try:
            result = handler(text)

            # 如果成功处理或有明确错误（不是"不是有效的命令"），则返回结果
            if result.get("success") or result.get("error") != "不是有效的命令":
                return result
        except Exception as e:
            logger.exception(f"命令处理失败: {handler.__name__}")
            return {"success": False, "error": f"命令处理失败: {str(e)}"}

    # 如果没有处理函数能处理该命令
    return {"success": False, "error": f"未知命令: {text.strip().split()[0]}"}


def format_response(result: Dict[str, Any]) -> str:
    """
    格式化响应结果为字符串

    Args:
        result: 命令执行结果

    Returns:
        str: 格式化后的响应字符串
    """
    if not result.get("success"):
        return f"Error: {result.get('error', '未知错误')}"

    # 如果有消息，直接返回
    if "message" in result:
        return result["message"]

    # 否则，格式化JSON结果
    return json.dumps(result, ensure_ascii=False, indent=2)
