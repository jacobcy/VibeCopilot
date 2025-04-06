"""
内容解析器适配层
提供多种内容解析器，支持规则、文档和通用内容的解析
"""

from adapters.content_parser.content_parser import ContentParser
from adapters.content_parser.openai import (
    OpenAIClient,
    OpenAIDocumentParser,
    OpenAIGenericParser,
    OpenAIParser,
    OpenAIRuleParser,
)

# 暴露的公共接口
__all__ = [
    "ContentParser",  # 主解析器
    "OpenAIClient",  # OpenAI API客户端
    "OpenAIParser",  # OpenAI基础解析器
    "OpenAIRuleParser",  # OpenAI规则解析器
    "OpenAIDocumentParser",  # OpenAI文档解析器
    "OpenAIGenericParser",  # OpenAI通用解析器
]
