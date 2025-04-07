"""
Basic Memory适配器配置文件
包含默认配置参数与常量
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 基本路径配置
DEFAULT_VAULT_PATH = os.path.expanduser("~/Documents/BasicMemory")
DEFAULT_EXPORT_PATH = os.path.expanduser("~/Documents/Obsidian")
DEFAULT_OUTPUT_PATH = os.path.expanduser("~/Documents/MemoryOutput")

# 解析器配置
DEFAULT_PARSER_CONFIG = {
    "max_tokens": 4096,
    "chunk_size": 1024,
    "overlap_size": 128,
    "include_metadata": True,
    "extract_entities": True,
    "extract_relations": True,
}

# Obsidian导出配置
DEFAULT_OBSIDIAN_CONFIG = {
    "create_index_files": True,
    "link_entities": True,
    "create_backlinks": True,
    "format": "markdown",
    "include_metadata": True,
    "use_wikilinks": True,
    "template_folder": "templates",
}

# 文件类型映射
FILE_TYPE_MAPPING = {
    "text": [".txt", ".md", ".rst", ".rtf"],
    "document": [".doc", ".docx", ".pdf", ".odt"],
    "spreadsheet": [".xls", ".xlsx", ".csv", ".ods"],
    "presentation": [".ppt", ".pptx", ".odp"],
    "code": [".py", ".js", ".html", ".css", ".ts", ".tsx", ".java", ".c", ".cpp", ".h"],
    "data": [".json", ".xml", ".yaml", ".yml"],
    "archive": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"],
    "audio": [".mp3", ".wav", ".ogg", ".flac"],
    "video": [".mp4", ".mkv", ".avi", ".mov"],
}

# 数据模型默认字段
DEFAULT_ENTITY_FIELDS = ["id", "name", "type", "description", "tags", "created_at", "updated_at"]

DEFAULT_RELATION_FIELDS = [
    "id",
    "source",
    "target",
    "type",
    "description",
    "tags",
    "created_at",
    "updated_at",
]

DEFAULT_OBSERVATION_FIELDS = ["id", "content", "source", "tags", "created_at", "updated_at"]

# 解析器类型映射
PARSER_TYPE_MAPPING = {
    "ollama": "OllamaParser",
    "llama": "LlamaParser",
    "gpt": "GptParser",
    "regex": "RegexParser",
    "simple": "SimpleParser",
    "auto": "AutoParser",
}

# 导出类型映射
EXPORTER_TYPE_MAPPING = {
    "obsidian": "ObsidianExporter",
    "markdown": "MarkdownExporter",
    "json": "JsonExporter",
    "csv": "CsvExporter",
    "text": "TextExporter",
}


def get_config(config_type: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取指定类型的配置，可选择覆盖默认配置

    Args:
        config_type: 配置类型，如"parser"或"obsidian"
        custom_config: 自定义配置，会覆盖默认配置

    Returns:
        Dict: 合并后的配置
    """
    config = {}

    if config_type == "parser":
        config = DEFAULT_PARSER_CONFIG.copy()
    elif config_type == "obsidian":
        config = DEFAULT_OBSIDIAN_CONFIG.copy()

    if custom_config:
        config.update(custom_config)

    return config
