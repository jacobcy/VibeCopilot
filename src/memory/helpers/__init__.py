#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆服务助手模块

提供记忆服务所需的工具函数，简化常见操作。
不包含数据库操作逻辑，这些逻辑已迁移到MemoryItemRepository类。
"""

# 导入数据库工具 (仅保留不直接操作具体数据模型的函数)
from .db_utils import create_tables, get_session, init_db_engine

# 导入笔记工具
from .note_utils import create_note, delete_note, read_note, update_note
from .path_helpers import (  # 路径基础操作; 文件名和路径验证; 目录操作; 路径关系和转换; 永久链接和URL相关; 文件信息
    ensure_dir_exists,
    expand_user_path,
    find_common_prefix,
    format_file_size,
    get_extension,
    get_file_info,
    get_file_size,
    get_filename,
    get_parent_dir,
    get_path_type,
    is_permalink,
    is_subpath,
    is_url,
    is_valid_filename,
    join_paths,
    list_files,
    make_relative_path,
    normalize_path,
    path_to_permalink,
    permalink_to_path,
    resolve_path,
    sanitize_filename,
)

# 导入同步工具
from .sync_tools import export_knowledge_base, get_sync_status, start_sync_watch, sync_directory, sync_file, sync_files

# 仅保留同步相关的工具函数
from .sync_utils import (
    create_diff_payload,
    create_sync_payload,
    get_sync_config,
    load_sync_payload,
    save_sync_config,
    save_sync_payload,
    update_last_sync_time,
)
from .text_helpers import (
    calculate_text_similarity,
    clean_text,
    contains_chinese,
    detect_language,
    extract_keywords,
    extract_plain_text,
    highlight_text,
    normalize_text,
    split_text,
    truncate_text,
)
from .time_helpers import (
    calculate_time_difference,
    datetime_to_timestamp,
    format_datetime,
    format_time_difference,
    get_current_datetime,
    get_current_timestamp,
    get_date_range,
    get_day_end,
    get_day_start,
    is_same_day,
    parse_datetime,
    parse_timeframe,
    timestamp_to_datetime,
)

__all__ = [
    # 路径基础操作
    "normalize_path",
    "join_paths",
    "get_parent_dir",
    "get_filename",
    "get_extension",
    # 文件名和路径验证
    "is_valid_filename",
    "sanitize_filename",
    # 目录操作
    "ensure_dir_exists",
    "list_files",
    # 路径关系和转换
    "is_subpath",
    "make_relative_path",
    "expand_user_path",
    "find_common_prefix",
    "resolve_path",
    # 永久链接和URL相关
    "path_to_permalink",
    "permalink_to_path",
    "is_url",
    "is_permalink",
    "get_path_type",
    # 文件信息
    "get_file_size",
    "format_file_size",
    "get_file_info",
    # 文本处理
    "clean_text",
    "normalize_text",
    "extract_plain_text",
    "truncate_text",
    "split_text",
    "extract_keywords",
    "calculate_text_similarity",
    "highlight_text",
    "contains_chinese",
    "detect_language",
    # 时间处理
    "get_current_timestamp",
    "get_current_datetime",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    "format_datetime",
    "parse_datetime",
    "parse_timeframe",
    "get_date_range",
    "calculate_time_difference",
    "format_time_difference",
    "is_same_day",
    "get_day_start",
    "get_day_end",
    # 数据库工具 (仅保留通用工具)
    "init_db_engine",
    "create_tables",
    "get_session",
    # 保留的同步工具 (sync_utils)
    "create_sync_payload",
    "save_sync_payload",
    "load_sync_payload",
    "get_sync_config",
    "save_sync_config",
    "update_last_sync_time",
    "create_diff_payload",
    # 笔记工具
    "create_note",
    "read_note",
    "update_note",
    "delete_note",
    # 同步工具 (sync_tools)
    "sync_file",
    "sync_files",
    "export_knowledge_base",
    "start_sync_watch",
    "sync_directory",
    "get_sync_status",
]
