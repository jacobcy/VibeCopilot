"""
Basic Memory适配器
提供文档解析、实体关系提取和导出功能
"""

from adapters.basic_memory.base import BaseExporter, BaseParser
from adapters.basic_memory.config import (
    DEFAULT_OBSIDIAN_CONFIG,
    DEFAULT_PARSER_CONFIG,
    EXPORTER_TYPE_MAPPING,
    PARSER_TYPE_MAPPING,
    get_config,
)
from adapters.basic_memory.utils.formatters import (
    convert_to_entity_format,
    print_entity_visualization,
)

# 暂时注释掉，等实现完成后再启用
# from adapters.basic_memory.memory_manager import MemoryManager

__version__ = "0.1.0"
__all__ = [
    # "MemoryManager", # 知识库管理器
    "BaseParser",
    "BaseExporter",
    "DEFAULT_PARSER_CONFIG",
    "DEFAULT_OBSIDIAN_CONFIG",
    "PARSER_TYPE_MAPPING",
    "EXPORTER_TYPE_MAPPING",
    "get_config",
    "convert_to_entity_format",
    "print_entity_visualization",
]
