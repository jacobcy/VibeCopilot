"""
解析器工厂

根据内容类型和后端类型创建合适的解析器实例。
"""

from typing import Any, Dict, Optional

from src.parsing.base_parser import BaseParser
from src.parsing.parsers.ollama_parser import OllamaParser
from src.parsing.parsers.openai_parser import OpenAIParser
from src.parsing.parsers.regex_parser import RegexParser


def create_parser(
    content_type: str = "generic", backend: str = "openai", config: Optional[Dict[str, Any]] = None
) -> BaseParser:
    """
    创建解析器实例

    Args:
        content_type: 内容类型，如'rule'、'document'、'generic'等
        backend: 后端类型，如'openai'、'ollama'、'regex'等
        config: 配置参数

    Returns:
        解析器实例

    Raises:
        ValueError: 如果指定的后端不存在
    """
    config = config or {}

    # 添加内容类型到配置中
    config["content_type"] = content_type

    # 根据后端类型创建解析器
    if backend == "openai":
        return OpenAIParser(config)
    elif backend == "ollama":
        return OllamaParser(config)
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
