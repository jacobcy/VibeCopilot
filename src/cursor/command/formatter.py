"""
结果格式化模块

提供命令结果格式化功能
"""

import logging
from typing import Any, Dict

from src.cursor.command.suggestions import get_error_suggestions_from_message

logger = logging.getLogger(__name__)


def generate_progress_bar(progress: float, width: int = 20) -> str:
    """生成进度条显示

    Args:
        progress: 进度百分比 (0-100)
        width: 进度条宽度

    Returns:
        str: 文本进度条
    """
    # 确保进度在0-100范围内
    progress = max(0, min(100, progress))
    filled = int(width * progress / 100)
    bar = "=" * filled + ">" + " " * (width - filled - 1)
    return f"[{bar}] {progress:.1f}%"


def generate_summary(result: Dict[str, Any]) -> str:
    """从结果生成简洁摘要

    Args:
        result: 结果字典

    Returns:
        str: 摘要文本
    """
    if not result.get("success", True):
        return f"❌ 操作失败: {result.get('error', '未知错误')}"

    command = result.get("command", "")
    if "created" in result:
        return f"✅ 已创建: {result['created']}"
    elif "updated" in result:
        return f"✅ 已更新: {result['updated']}"
    elif "deleted" in result:
        return f"✅ 已删除: {result['deleted']}"
    elif "list" in result:
        count = len(result["list"]) if isinstance(result["list"], list) else "多个"
        return f"📋 已列出 {count} 个项目"
    else:
        return f"✅ 命令执行成功"


def enhance_result_for_agent(result: Dict[str, Any]) -> Dict[str, Any]:
    """增强结果以便AI agent更好地处理

    Args:
        result: 原始结果字典

    Returns:
        Dict[str, Any]: 增强后的结果字典
    """
    # 如果结果已经包含成功标志
    if "success" not in result:
        result["success"] = True

    # 如果操作失败，添加建议
    if result.get("success") is False and "suggestions" not in result:
        if "error" in result:
            result["suggestions"] = get_error_suggestions_from_message(result["error"])

    # 添加进度信息（如果有）
    if "progress" in result and isinstance(result["progress"], (int, float)):
        progress = result["progress"]
        progress_bar = generate_progress_bar(progress)
        result["progress_display"] = progress_bar

    # 添加AI友好的摘要
    if "summary" not in result:
        result["summary"] = generate_summary(result)

    return result


def format_help_text(command_name: str, help_text: str) -> str:
    """格式化帮助文本

    Args:
        command_name: 命令名称
        help_text: 原始帮助文本

    Returns:
        str: 格式化后的帮助文本
    """
    title = f"### {command_name} 命令帮助\n\n"
    formatted_text = help_text.strip()

    # 添加代码块格式
    if "用法:" in formatted_text:
        # 按行分割
        lines = formatted_text.split("\n")
        in_usage = False
        for i, line in enumerate(lines):
            if line.strip() == "用法:":
                in_usage = True
                lines[i] = "**用法:**\n```"
            elif in_usage and (line.strip() == "" or line.strip().startswith("选项:")):
                in_usage = False
                # 在空行或选项行前插入代码块结束标记
                lines[i] = "```\n" + line

        formatted_text = "\n".join(lines)

    # 添加选项高亮
    if "选项:" in formatted_text:
        lines = formatted_text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("--"):
                # 高亮选项
                option_parts = line.strip().split(" ", 1)
                if len(option_parts) > 1:
                    option, desc = option_parts
                    lines[i] = f"- **`{option}`**: {desc}"

        formatted_text = "\n".join(lines)

    return title + formatted_text


def format_error_response(error_msg: str, suggestions: list) -> Dict[str, Any]:
    """格式化错误响应

    Args:
        error_msg: 错误消息
        suggestions: 建议列表

    Returns:
        Dict[str, Any]: 格式化的错误响应
    """
    error_text = f"❌ **错误**: {error_msg}\n\n"

    if suggestions:
        error_text += "**建议**:\n"
        for suggestion in suggestions:
            error_text += f"- {suggestion}\n"

    return {
        "success": False,
        "error": error_msg,
        "formatted_message": error_text,
        "suggestions": suggestions,
    }
