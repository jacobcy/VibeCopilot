"""
工具函数 (兼容层)

提供内容解析的工具函数。此模块为兼容层，新代码应直接使用utils包中的模块。
"""

import logging
from typing import Any, Dict, Optional

from adapters.content_parser.utils.detector import detect_content_type
from adapters.content_parser.utils.parser import parse_content, parse_file
from adapters.content_parser.utils.storage import (
    save_document_to_database,
    save_rule_to_database,
    save_to_database,
)

# 创建日志记录器
logger = logging.getLogger(__name__)

# 为保持向后兼容性，导出原有函数
_detect_content_type = detect_content_type
_save_to_database = save_to_database
_save_rule_to_database = save_rule_to_database
_save_document_to_database = save_document_to_database

# 导出所有函数
__all__ = [
    "parse_file",
    "parse_content",
    "_detect_content_type",
    "_save_to_database",
    "_save_rule_to_database",
    "_save_document_to_database",
]
