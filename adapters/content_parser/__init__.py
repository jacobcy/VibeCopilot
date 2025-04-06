"""
内容解析模块
提供统一的接口用于解析Markdown文档和规则文件
"""

from adapters.content_parser.parser_factory import create_parser, get_default_parser
from adapters.content_parser.utils import parse_content, parse_file

__all__ = [
    "create_parser",
    "get_default_parser",
    "parse_file",
    "parse_content",
]
