#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步工具辅助模块

提供与Basic Memory同步相关的功能，如创建同步负载、管理同步配置等。
(移除了直接访问数据库的函数，相关逻辑已迁移到 MemoryItemRepository)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# 移除了 sqlalchemy 和 MemoryItem 的导入，因为数据库操作已移走
# from sqlalchemy import and_
# from sqlalchemy.orm import Session
# from src.models.db.memory_item import MemoryItem, SyncStatus

# 保留可能被其他 helpers 或 service 使用的非数据库工具函数
# from ..helpers import db_utils, normalize_path, is_permalink, path_to_permalink
# 注意：如果这些函数在其他地方没有被导入，也可以移除

logger = logging.getLogger(__name__)


def create_sync_payload(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    创建同步负载内容

    Args:
        items: 需要同步的项目列表

    Returns:
        Dict[str, Any]: 同步负载
    """
    return {"version": "1.0", "created_at": datetime.now().isoformat(), "items": items, "item_count": len(items)}


def save_sync_payload(payload: Dict[str, Any], file_path: str) -> bool:
    """
    保存同步负载到文件

    Args:
        payload: 同步负载内容
        file_path: 保存路径

    Returns:
        bool: 保存成功返回True，失败返回False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        logger.info(f"同步负载已保存到 {file_path}")
        return True

    except Exception as e:
        logger.error(f"保存同步负载失败: {str(e)}")
        return False


def load_sync_payload(file_path: str) -> Optional[Dict[str, Any]]:
    """
    从文件加载同步负载

    Args:
        file_path: 文件路径

    Returns:
        Optional[Dict[str, Any]]: 成功返回负载内容，失败返回None
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"同步负载文件不存在: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        logger.info(f"从 {file_path} 加载了同步负载")
        return payload

    except Exception as e:
        logger.error(f"加载同步负载失败: {str(e)}")
        return None


def get_sync_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    获取同步配置信息

    Args:
        config_path: 配置文件路径，如果为None则使用默认路径

    Returns:
        Dict[str, Any]: 同步配置
    """
    if config_path is None:
        # 使用默认配置路径
        home_dir = os.path.expanduser("~")
        config_path = os.path.join(home_dir, ".vibecopilot", "sync_config.json")

    # 如果配置文件不存在，返回默认配置
    if not os.path.exists(config_path):
        logger.warning(f"同步配置文件不存在: {config_path}，使用默认配置")
        return {"auto_sync": False, "sync_interval": 3600, "default_project": "vibecopilot", "default_folder": "Notes", "last_sync": None}  # 1小时

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        logger.debug(f"加载了同步配置: {config_path}")
        return config

    except Exception as e:
        logger.error(f"加载同步配置失败: {str(e)}")
        return {"auto_sync": False, "sync_interval": 3600, "default_project": "vibecopilot", "default_folder": "Notes", "last_sync": None}


def save_sync_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    保存同步配置

    Args:
        config: 配置信息
        config_path: 配置文件路径，如果为None则使用默认路径

    Returns:
        bool: 保存成功返回True，失败返回False
    """
    if config_path is None:
        # 使用默认配置路径
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".vibecopilot")
        config_path = os.path.join(config_dir, "sync_config.json")

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 更新最后修改时间
        config["updated_at"] = datetime.now().isoformat()

        # 写入文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"同步配置已保存到 {config_path}")
        return True

    except Exception as e:
        logger.error(f"保存同步配置失败: {str(e)}")
        return False


def update_last_sync_time(config_path: Optional[str] = None) -> bool:
    """
    更新最后同步时间

    Args:
        config_path: 配置文件路径，如果为None则使用默认路径

    Returns:
        bool: 更新成功返回True，失败返回False
    """
    try:
        # 获取当前配置
        config = get_sync_config(config_path)

        # 更新最后同步时间
        config["last_sync"] = datetime.now().isoformat()

        # 保存配置
        return save_sync_config(config, config_path)

    except Exception as e:
        logger.error(f"更新最后同步时间失败: {str(e)}")
        return False


def create_diff_payload(old_items: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    创建差异同步负载

    Args:
        old_items: 旧项目列表
        new_items: 新项目列表

    Returns:
        Dict[str, Any]: 差异同步负载
    """
    # 创建ID映射以便快速查找
    old_map = {item.get("id"): item for item in old_items if "id" in item}
    new_map = {item.get("id"): item for item in new_items if "id" in item}

    # 查找添加、更新和删除的项目
    added = [item for item in new_items if item.get("id") not in old_map]
    updated = []
    deleted_ids = []

    # 查找更新和删除的项目
    for item_id, old_item in old_map.items():
        if item_id in new_map:
            # 项目存在于新列表中，检查是否有更新
            new_item = new_map[item_id]
            if new_item != old_item:
                updated.append(new_item)
        else:
            # 项目不存在于新列表中，已删除
            deleted_ids.append(item_id)

    # 创建差异负载
    diff_payload = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "added": added,
        "updated": updated,
        "deleted": deleted_ids,
        "added_count": len(added),
        "updated_count": len(updated),
        "deleted_count": len(deleted_ids),
    }

    return diff_payload


# 以下函数已被移除，逻辑迁移至 MemoryItemRepository:
# - sync_item_from_remote
# - mark_item_synced
# - get_unsynced_items
# - get_item_by_title

# 注意：如果这些函数在其他地方没有被导入，也可以移除
