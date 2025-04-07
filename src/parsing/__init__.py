"""
统一内容解析框架

提供一致的接口解析各种内容类型，包括规则、文档和通用内容。
"""

from src.parsing.base_parser import BaseParser
from src.parsing.parser_factory import create_parser

__all__ = ["BaseParser", "create_parser"]
