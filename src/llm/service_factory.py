"""
LLM服务工厂

根据配置创建适当的LLM服务实例。
"""

from typing import Any, Dict, Optional

from src.llm.openai_service import OpenAIService
from src.llm.providers.ollama_service import OllamaService


def create_llm_service(provider: str = "openai", config: Optional[Dict[str, Any]] = None) -> Any:
    """
    创建LLM服务实例

    Args:
        provider: LLM服务提供者，如 'openai', 'ollama'
        config: 配置参数

    Returns:
        LLM服务实例

    Raises:
        ValueError: 如果指定的提供者不受支持
    """
    config = config or {}

    if provider == "openai":
        return OpenAIService()
    elif provider == "ollama":
        return OllamaService(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
