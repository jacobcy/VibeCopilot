"""
内容解析工具包

提供内容解析的工具函数
"""

from adapters.content_parser.utils.detector import detect_content_type, detect_content_type_from_text
from adapters.content_parser.utils.parser import parse_content, parse_file
from adapters.content_parser.utils.storage import save_document_to_database, save_rule_to_database, save_to_database

__all__ = [
    # 检测函数
    "detect_content_type",
    "detect_content_type_from_text",
    # 解析函数
    "parse_file",
    "parse_content",
    # 存储函数
    "save_to_database",
    "save_rule_to_database",
    "save_document_to_database",
]
