"""
解析器工厂
根据配置创建相应的内容解析器
"""

import logging
import os
from typing import Optional

from adapters.content_parser.base_parser import ContentParser

logger = logging.getLogger(__name__)


def create_parser(parser_type: str = "openai", model: Optional[str] = None, content_type: str = "generic") -> ContentParser:
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
        except ImportError:
            logger.error("OpenAI库未安装或版本不兼容，无法使用OpenAI解析器")
            raise ValueError("OpenAI库未安装或版本不兼容") from ImportError
        except Exception as e:
            logger.error(f"创建解析器失败: {e}")
            raise ValueError(f"创建解析器失败: {e}") from e

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
    try:
        parser_type = os.environ.get("VIBE_CONTENT_PARSER", "openai")
        if parser_type == "openai":
            model = os.environ.get("VIBE_OPENAI_MODEL")
            from adapters.content_parser.openai_parser import OpenAIParser

            return OpenAIParser(model, content_type)
        elif parser_type == "ollama":
            model = os.environ.get("VIBE_OLLAMA_MODEL", "mistral")
            from adapters.content_parser.ollama_parser import OllamaParser

            return OllamaParser(model, content_type)
        else:
            logger.error(f"不支持的默认解析器类型: {parser_type}")
            raise ValueError(f"不支持的默认解析器类型: {parser_type}")
    except Exception as e:
        logger.error(f"获取默认解析器失败: {e}")
        raise ValueError("无法确定默认解析器") from e


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
    except FileNotFoundError:
        # .env 文件不存在是正常情况
        pass
    except Exception as e:
        # 记录其他可能的读取错误
        logger.warning(f"检查 .env 文件时出错: {e}")
        pass

    return False
