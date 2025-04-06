"""
适配器模块
提供与外部系统集成的接口
"""

# 内容解析适配器
from adapters.content_parser import parse_content, parse_file
from adapters.docs_engine import (
    extract_document_blocks,
    import_document_to_db,
    parse_document_content,
    parse_document_file,
)
from adapters.n8n import N8nAdapter
from adapters.rule_engine import detect_rule_conflicts, parse_rule_content, parse_rule_file

# 外部系统集成
from adapters.status_sync import StatusSyncAdapter

__all__ = [
    # 内容解析
    "parse_file",
    "parse_content",
    "parse_rule_file",
    "parse_rule_content",
    "detect_rule_conflicts",
    "parse_document_file",
    "parse_document_content",
    "extract_document_blocks",
    "import_document_to_db",
    # 外部集成
    "StatusSyncAdapter",
    "N8nAdapter",
]
