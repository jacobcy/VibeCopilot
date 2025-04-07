"""
Ollama 内容解析器子模块

提供使用 Ollama 服务解析各种内容的功能
"""

from adapters.content_parser.ollama.document_parser import parse_document
from adapters.content_parser.ollama.generic_parser import parse_generic
from adapters.content_parser.ollama.parser import OllamaParser
from adapters.content_parser.ollama.rule_parser import parse_rule

__all__ = ["OllamaParser", "parse_document", "parse_rule", "parse_generic"]
