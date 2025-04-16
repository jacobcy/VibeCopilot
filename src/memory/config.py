#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆服务配置模块

提供记忆服务所需的配置项管理功能，包括数据库路径、BasicMemory配置等。
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    # 数据库配置
    "db_path": os.path.expanduser("~/.vibe_copilot/memory.db"),
    "db_init_schema": True,
    # Basic Memory配置
    "basic_memory_enabled": True,
    "basic_memory_default_folder": "VibeCopilot",
    # 同步配置
    "sync_on_startup": False,
    "sync_interval": 3600,  # 秒，默认1小时
    # 搜索配置
    "search_max_results": 50,
    "search_fuzzy_match": True,
    # 缓存配置
    "cache_enabled": True,
    "cache_ttl": 300,  # 秒，默认5分钟
}

# 全局配置对象
_config = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件，如果文件不存在则使用默认配置

    Args:
        config_path: 配置文件路径，默认为~/.vibe_copilot/memory_config.json

    Returns:
        配置字典
    """
    global _config

    if _config is not None:
        return _config

    if config_path is None:
        config_path = os.path.expanduser("~/.vibe_copilot/memory_config.json")

    config = DEFAULT_CONFIG.copy()

    # 尝试加载配置文件
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                config.update(user_config)
            logger.info(f"已加载记忆服务配置: {config_path}")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，将使用默认配置")
    else:
        logger.info(f"配置文件不存在: {config_path}，将使用默认配置")

        # 确保配置目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 保存默认配置
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            logger.info(f"已保存默认配置到: {config_path}")
        except Exception as e:
            logger.warning(f"保存默认配置失败: {e}")

    # 确保数据库目录存在
    db_dir = os.path.dirname(config["db_path"])
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"已创建数据库目录: {db_dir}")

    _config = config
    return config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    保存配置到文件

    Args:
        config: 配置字典
        config_path: 配置文件路径，默认为~/.vibe_copilot/memory_config.json

    Returns:
        是否保存成功
    """
    global _config

    if config_path is None:
        config_path = os.path.expanduser("~/.vibe_copilot/memory_config.json")

    # 确保配置目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"已保存配置到: {config_path}")
        _config = config
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


def get_config() -> Dict[str, Any]:
    """
    获取当前配置

    Returns:
        配置字典
    """
    global _config

    if _config is None:
        return load_config()

    return _config


def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新配置并保存

    Args:
        updates: 要更新的配置项

    Returns:
        更新后的配置字典
    """
    config = get_config()
    config.update(updates)
    save_config(config)
    return config


def get_db_path() -> str:
    """
    获取数据库路径

    Returns:
        数据库路径
    """
    return get_config().get("db_path", DEFAULT_CONFIG["db_path"])


def set_db_path(path: str) -> bool:
    """
    设置数据库路径

    Args:
        path: 新的数据库路径

    Returns:
        是否设置成功
    """
    return update_config({"db_path": path}) is not None
