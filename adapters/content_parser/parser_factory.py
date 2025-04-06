"""
解析器工厂
根据配置创建相应的内容解析器
"""

import logging
import os
from typing import Optional

from adapters.content_parser.base_parser import ContentParser

logger = logging.getLogger(__name__)


def create_parser(
    parser_type: str = "openai", model: Optional[str] = None, content_type: str = "generic"
) -> ContentParser:
    """创建内容解析器

    Args:
        parser_type: 解析器类型 ("openai" 或 "ollama")
        model: 模型名称，如不指定则使用环境变量或默认值
        content_type: 内容类型 ("rule", "document", "generic")

    Returns:
        ContentParser: 内容解析器实例
    """
    # 获取模型名称
    if not model:
        if parser_type == "openai":
            model = os.environ.get("VIBE_OPENAI_MODEL", "gpt-4o-mini")
        else:
            model = os.environ.get("VIBE_OLLAMA_MODEL", "mistral")

    logger.info(f"创建{parser_type}解析器，模型:{model}，内容类型:{content_type}")

    # 创建解析器
    if parser_type == "openai":
        from adapters.content_parser.openai_parser import OpenAIParser

        try:
            return OpenAIParser(model, content_type)
        except Exception as e:
            logger.warning(f"创建OpenAI解析器失败: {e}，尝试回退到Ollama")
            if content_type == "rule":
                logger.info("对于规则解析，回退到Ollama解析器")
                from adapters.content_parser.ollama_parser import OllamaParser

                return OllamaParser(os.environ.get("VIBE_OLLAMA_MODEL", "mistral"), content_type)
            else:
                raise

    elif parser_type == "ollama":
        from adapters.content_parser.ollama_parser import OllamaParser

        return OllamaParser(model, content_type)
    else:
        raise ValueError(f"不支持的解析器类型: {parser_type}")


def get_default_parser(content_type: str = "generic") -> ContentParser:
    """获取默认的内容解析器

    基于环境变量配置或默认使用OpenAI

    Args:
        content_type: 内容类型 ("rule", "document", "generic")

    Returns:
        ContentParser: 默认的内容解析器
    """
    # 从环境变量获取默认解析器类型
    parser_type = os.environ.get("VIBE_CONTENT_PARSER", "openai")

    # 如果OpenAI API密钥不可用且默认为OpenAI，则回退到Ollama
    if parser_type == "openai" and not os.environ.get("OPENAI_API_KEY"):
        # 检查.env文件中是否有API密钥
        if not _check_openai_key_in_env_file():
            logger.warning("OpenAI API密钥不可用，回退到Ollama解析器")
            parser_type = "ollama"

    logger.info(f"使用默认解析器类型: {parser_type}，内容类型: {content_type}")
    return create_parser(parser_type, content_type=content_type)


def _check_openai_key_in_env_file() -> bool:
    """检查.env文件中是否有OpenAI API密钥

    Returns:
        bool: 是否有可用的API密钥
    """
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("OPENAI_API_KEY="):
                    api_key = line.strip().split("=", 1)[1].strip('"').strip("'")
                    return bool(api_key)
    except:
        pass

    return False
