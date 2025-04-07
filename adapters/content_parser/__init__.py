"""
统一内容解析器模块 - 直接转发到新的统一解析框架

此模块已被 src.parsing 替代，此文件仅做转发以保持最小兼容性。
"""

from src.parsing import BaseParser, create_parser
from src.parsing.parsers.ollama_parser import OllamaParser
from src.parsing.parsers.openai_parser import OpenAIParser
from src.parsing.parsers.regex_parser import RegexParser

# 为了简单兼容，保留 ContentParser 类名
ContentParser = BaseParser


# 兼容函数
def parse_file(file_path, content_type=None, backend="openai"):
    """解析文件内容 (兼容函数)"""
    parser = create_parser("generic", backend)
    return parser.parse_file(file_path, content_type)


def parse_content(content, content_type=None, backend="openai"):
    """解析文本内容 (兼容函数)"""
    parser = create_parser("generic", backend)
    return parser.parse_text(content, content_type)


# 导出所有需要的内容
__all__ = [
    "ContentParser",
    "BaseParser",
    "OpenAIParser",
    "OllamaParser",
    "RegexParser",
    "create_parser",
    "parse_file",
    "parse_content",
]
