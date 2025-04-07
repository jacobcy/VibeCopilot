"""
命令建议模块

提供命令建议生成功能
"""

import difflib
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_similar_commands(cmd: str, command_list: List[str]) -> List[str]:
    """查找相似命令

    Args:
        cmd: 用户输入的命令
        command_list: 可用命令列表

    Returns:
        相似命令列表
    """
    # 使用difflib查找相似命令
    matches = difflib.get_close_matches(cmd, command_list, n=3, cutoff=0.6)
    return matches


def get_command_suggestions(command: str, available_commands: List[Dict[str, Any]]) -> List[str]:
    """根据错误的命令提供建议

    Args:
        command: 输入的命令
        available_commands: 可用命令列表

    Returns:
        建议列表
    """
    suggestions = []
    try:
        # 基本命令格式建议
        if not command.startswith("/"):
            suggestions.append("命令必须以'/'开头，例如: /help")

        parts = command.strip().split()
        if len(parts) > 0:
            cmd = parts[0].lstrip("/")

            # 检查是否是已知命令
            command_names = [c["name"] for c in available_commands]

            # 如果不是已知命令，推荐相似命令
            if cmd not in command_names:
                similar = get_similar_commands(cmd, command_names)
                if similar:
                    suggestions.append(f"您是否想使用: {', '.join(['/' + s for s in similar])}")

            # 添加命令帮助提示
            suggestions.append(f"尝试使用 '/help {cmd}' 获取命令帮助")

    except Exception as e:
        logger.error(f"生成命令建议时出错: {str(e)}")
        # 如果建议生成过程出错，提供通用建议
        suggestions.append("尝试使用 '/help' 查看所有可用命令")

    if not suggestions:
        suggestions.append("尝试使用 '/help' 查看所有可用命令")

    return suggestions


def get_error_suggestions(error: Exception) -> List[str]:
    """根据错误提供建议

    Args:
        error: 异常对象

    Returns:
        建议列表
    """
    error_msg = str(error)
    return get_error_suggestions_from_message(error_msg)


def get_error_suggestions_from_message(error_msg: str) -> List[str]:
    """根据错误消息提供建议

    Args:
        error_msg: 错误消息

    Returns:
        建议列表
    """
    suggestions = []

    # 根据错误消息模式匹配建议
    if "找不到命令" in error_msg or "unknown command" in error_msg.lower():
        suggestions.append("使用 '/help' 查看所有可用命令")
    elif "权限" in error_msg or "permission" in error_msg.lower():
        suggestions.append("确保您有执行此操作的权限")
    elif "缺少参数" in error_msg or "missing argument" in error_msg.lower():
        # 尝试从错误消息中提取参数名
        param_match = re.search(r"['\"]([^'\"]+)['\"]", error_msg)
        if param_match:
            param_name = param_match.group(1)
            suggestions.append(f"命令缺少必要参数: {param_name}")
        else:
            suggestions.append("命令缺少必要参数，请检查命令格式")
    elif "无法连接" in error_msg or "could not connect" in error_msg.lower():
        suggestions.append("检查网络连接是否正常")
        suggestions.append("确保服务已启动")
    elif "找不到文件" in error_msg or "file not found" in error_msg.lower():
        file_match = re.search(r"['\"]([^'\"]+)['\"]", error_msg)
        if file_match:
            file_path = file_match.group(1)
            suggestions.append(f"找不到文件: {file_path}，请检查文件路径是否正确")
        else:
            suggestions.append("找不到指定的文件，请检查文件路径是否正确")
    else:
        # 无法识别的错误，给出通用建议
        suggestions.append("检查命令格式是否正确")
        suggestions.append("使用 '/help <命令名>' 获取特定命令的帮助")

    return suggestions
