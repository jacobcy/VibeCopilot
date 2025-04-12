"""
解析器工厂

根据内容类型和提供者类型创建合适的解析器实例。
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.parsing.base_parser import BaseParser
from src.parsing.parsers.llm_parser import LLMParser
from src.parsing.parsers.regex_parser import RegexParser


def create_parser(content_type: str = "generic", backend: str = "openai", config: Optional[Dict[str, Any]] = None) -> BaseParser:
    """
    创建解析器实例

    Args:
        content_type: 内容类型，如'rule'、'document'、'generic'等
        backend: 提供者类型，如'openai'、'ollama'、'regex'等
        config: 配置参数

    Returns:
        解析器实例

    Raises:
        ValueError: 如果指定的提供者不存在
    """
    config = config or {}

    # 添加内容类型到配置中
    config["content_type"] = content_type

    # 根据提供者类型创建解析器
    if backend in ["openai", "ollama"]:
        # 添加提供者信息到配置中
        config["provider"] = backend
        return LLMParser(config)
    elif backend == "regex":
        return RegexParser(config)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def get_default_parser(config: Optional[Dict[str, Any]] = None) -> BaseParser:
    """
    获取默认解析器

    使用配置中指定的默认后端和内容类型创建解析器。

    Args:
        config: 配置参数

    Returns:
        默认解析器实例
    """
    config = config or {}

    # 从配置中获取默认后端和内容类型
    default_backend = config.get("default_backend", "openai")
    default_content_type = config.get("default_content_type", "generic")

    return create_parser(default_content_type, default_backend, config)


def get_parser_for_file(file_path: str, config: Optional[Dict[str, Any]] = None) -> BaseParser:
    """
    根据文件路径获取合适的解析器

    根据文件扩展名和内容自动选择最合适的解析器

    Args:
        file_path: 文件路径
        config: 配置参数

    Returns:
        解析器实例
    """
    config = config or {}

    # 获取文件扩展名
    ext = Path(file_path).suffix.lower()

    # 根据扩展名确定内容类型
    content_type = "generic"
    if ext in [".md", ".mdc", ".markdown"]:
        content_type = "rule" if "rule" in file_path.lower() else "document"
    elif ext in [".json", ".yaml", ".yml"]:
        content_type = "data"
    elif ext in [".py", ".js", ".ts", ".java", ".c", ".cpp"]:
        content_type = "code"

    # 选择解析器提供者
    # 对于复杂格式（如MDC），使用LLM解析
    if ext in [".md", ".mdc", ".markdown"]:
        backend = config.get("default_backend", "openai")
    # 对于结构化数据，可以使用正则表达式或其他简单解析
    elif ext in [".json", ".yaml", ".yml"]:
        backend = "regex"
    # 默认使用OpenAI
    else:
        backend = config.get("default_backend", "openai")

    # 添加文件信息到配置
    config["file_path"] = file_path
    config["file_extension"] = ext
    config["content_type"] = content_type

    # 创建并返回解析器
    return create_parser(content_type, backend, config)
