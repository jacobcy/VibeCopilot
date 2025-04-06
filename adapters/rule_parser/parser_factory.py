"""
解析器工厂
根据配置创建相应的规则解析器
"""

import os
from typing import Optional

from adapters.rule_parser.base_parser import RuleParser


def create_parser(parser_type: str = "openai", model: str = None) -> RuleParser:
    """创建规则解析器

    Args:
        parser_type: 解析器类型 ("openai" 或 "ollama")
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        RuleParser: 规则解析器实例
    """
    # 获取模型名称
    if not model:
        if parser_type == "openai":
            model = os.environ.get("VIBE_OPENAI_MODEL", "gpt-4o-mini")
        else:
            model = os.environ.get("VIBE_OLLAMA_MODEL", "mistral")

    # 创建解析器
    if parser_type == "openai":
        from adapters.rule_parser.openai_rule_parser import OpenAIRuleParser

        return OpenAIRuleParser(model)
    elif parser_type == "ollama":
        from adapters.rule_parser.ollama_rule_parser import OllamaRuleParser

        return OllamaRuleParser(model)
    else:
        raise ValueError(f"不支持的解析器类型: {parser_type}")


def get_default_parser() -> RuleParser:
    """获取默认的规则解析器

    基于环境变量配置或默认使用OpenAI

    Returns:
        RuleParser: 默认的规则解析器
    """
    # 从环境变量获取默认解析器类型
    parser_type = os.environ.get("VIBE_RULE_PARSER", "openai")

    # 如果OpenAI API密钥不可用且默认为OpenAI，则回退到Ollama
    if parser_type == "openai" and not os.environ.get("OPENAI_API_KEY"):
        # 检查.env文件中是否有API密钥
        if not _check_openai_key_in_env_file():
            print("OpenAI API密钥不可用，回退到Ollama解析器")
            parser_type = "ollama"

    return create_parser(parser_type)


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
