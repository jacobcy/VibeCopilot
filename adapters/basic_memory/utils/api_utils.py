#!/usr/bin/env python3
"""
API工具模块
提供与API交互的辅助函数
"""

import os
from typing import Optional


def get_openai_api_key() -> Optional[str]:
    """获取OpenAI API密钥

    从环境变量中获取OpenAI API密钥。
    优先级: OPENAI_API_KEY > OPENAI_KEY

    Returns:
        str: API密钥，如果未找到则返回None
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    return api_key


def get_api_base_url(provider: str = "openai") -> Optional[str]:
    """获取API基础URL

    Args:
        provider: API提供商，如"openai"、"azure"等

    Returns:
        str: API基础URL，如果未找到则返回None
    """
    if provider.lower() == "openai":
        return os.environ.get("OPENAI_API_BASE") or "https://api.openai.com/v1"
    elif provider.lower() == "azure":
        return os.environ.get("AZURE_OPENAI_ENDPOINT")
    elif provider.lower() == "anthropic":
        return os.environ.get("ANTHROPIC_API_BASE") or "https://api.anthropic.com"

    return None


def get_api_key(provider: str = "openai") -> Optional[str]:
    """获取指定提供商的API密钥

    Args:
        provider: API提供商，如"openai"、"azure"、"anthropic"等

    Returns:
        str: API密钥，如果未找到则返回None
    """
    if provider.lower() == "openai":
        return get_openai_api_key()
    elif provider.lower() == "azure":
        return os.environ.get("AZURE_OPENAI_API_KEY")
    elif provider.lower() == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY")

    return None
