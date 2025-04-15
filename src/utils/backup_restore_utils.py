#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库备份恢复工具模块

提供数据库实体的备份和恢复功能，支持JSON和SQLite格式。
"""

import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.init_db import get_db_path
from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file

logger = logging.getLogger(__name__)


class EntityBackupRestoreHandler(ABC):
    """实体备份恢复处理器基类"""

    def __init__(self, entity_type: str):
        """
        初始化实体备份恢复处理器

        Args:
            entity_type: 实体类型名称
        """
        self.entity_type = entity_type
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def get_repository(self, session: Session) -> Repository:
        """
        获取实体仓库

        Args:
            session: 数据库会话

        Returns:
            Repository: 实体仓库实例
        """
        pass

    def backup(self, session: Session, output_path: str, format: str = "json") -> Dict[str, Any]:
        """
        备份指定类型的实体

        Args:
            session: 数据库会话
            output_path: 输出路径
            format: 输出格式，支持json和sqlite

        Returns:
            Dict[str, Any]: 备份结果统计
        """
        self.logger.info(f"开始备份 {self.entity_type} 实体 (格式: {format})")

        if format == "json":
            return self._backup_to_json(session, output_path)
        elif format == "sqlite":
            return self._backup_to_sqlite(session, output_path)
        else:
            raise ValueError(f"不支持的备份格式: {format}")

    def restore(self, session: Session, input_path: str, format: str = "json", force: bool = False) -> Dict[str, Any]:
        """
        恢复指定类型的实体

        Args:
            session: 数据库会话
            input_path: 输入路径
            format: 输入格式，支持json和sqlite
            force: 是否强制覆盖已存在的数据

        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        self.logger.info(f"开始恢复 {self.entity_type} 实体 (格式: {format})")

        if format == "json":
            return self._restore_from_json(session, input_path, force)
        elif format == "sqlite":
            return self._restore_from_sqlite(session, input_path, force)
        else:
            raise ValueError(f"不支持的恢复格式: {format}")

    def _backup_to_json(self, session: Session, output_path: str) -> Dict[str, Any]:
        """
        将实体备份为JSON格式

        Args:
            session: 数据库会话
            output_path: 输出路径

        Returns:
            Dict[str, Any]: 备份结果统计
        """
        repo = self.get_repository(session)
        entities = repo.get_all()

        # 确保输出目录存在
        ensure_directory_exists(output_path)

        count = 0
        for entity in entities:
            entity_dict = entity.to_dict()
            entity_id = entity_dict.get("id")

            if not entity_id:
                self.logger.warning(f"实体缺少ID字段，跳过")
                continue

            file_path = os.path.join(output_path, f"{entity_id}.json")
            write_json_file(file_path, entity_dict)
            count += 1

        result = {
            "entity_type": self.entity_type,
            "format": "json",
            "count": count,
            "output_path": output_path,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"成功备份 {count} 个 {self.entity_type} 实体到 {output_path}")
        return result

    def _backup_to_sqlite(self, session: Session, output_path: str) -> Dict[str, Any]:
        """
        将实体备份为SQLite格式

        Args:
            session: 数据库会话
            output_path: 输出路径

        Returns:
            Dict[str, Any]: 备份结果统计
        """
        # 获取原始数据库路径
        db_path = get_db_path()

        # 复制数据库文件
        shutil.copy2(db_path, output_path)

        result = {"entity_type": self.entity_type, "format": "sqlite", "output_path": output_path, "timestamp": datetime.now().isoformat()}

        self.logger.info(f"成功备份数据库到 {output_path}")
        return result

    def _restore_from_json(self, session: Session, input_path: str, force: bool = False) -> Dict[str, Any]:
        """
        从JSON格式恢复实体

        Args:
            session: 数据库会话
            input_path: 输入路径
            force: 是否强制覆盖已存在的数据

        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        repo = self.get_repository(session)

        # 检查输入路径是文件还是目录
        if os.path.isfile(input_path):
            # 单个文件
            return self._restore_json_file(repo, input_path, force)
        elif os.path.isdir(input_path):
            # 目录
            return self._restore_json_directory(repo, input_path, force)
        else:
            raise ValueError(f"输入路径不存在: {input_path}")

    def _restore_json_file(self, repo: Repository, file_path: str, force: bool = False) -> Dict[str, Any]:
        """
        恢复单个JSON文件

        Args:
            repo: 实体仓库
            file_path: 文件路径
            force: 是否强制覆盖已存在的数据

        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        try:
            data = read_json_file(file_path)
            entity_id = data.get("id")

            if not entity_id:
                raise ValueError(f"JSON文件缺少ID字段: {file_path}")

            # 检查是否已存在
            existing = repo.get_by_id(entity_id)

            if existing and not force:
                self.logger.info(f"实体已存在且force=False，跳过: {entity_id}")
                return {
                    "entity_type": self.entity_type,
                    "format": "json",
                    "file": file_path,
                    "imported": 0,
                    "updated": 0,
                    "skipped": 1,
                    "timestamp": datetime.now().isoformat(),
                }

            if existing:
                # 更新现有实体
                repo.update(entity_id, data)
                result = {
                    "entity_type": self.entity_type,
                    "format": "json",
                    "file": file_path,
                    "imported": 0,
                    "updated": 1,
                    "skipped": 0,
                    "timestamp": datetime.now().isoformat(),
                }
                self.logger.info(f"更新实体: {entity_id}")
            else:
                # 创建新实体
                repo.create(data)
                result = {
                    "entity_type": self.entity_type,
                    "format": "json",
                    "file": file_path,
                    "imported": 1,
                    "updated": 0,
                    "skipped": 0,
                    "timestamp": datetime.now().isoformat(),
                }
                self.logger.info(f"导入实体: {entity_id}")

            return result

        except Exception as e:
            self.logger.error(f"恢复JSON文件失败: {file_path}, 错误: {str(e)}")
            raise

    def _restore_json_directory(self, repo: Repository, dir_path: str, force: bool = False) -> Dict[str, Any]:
        """
        恢复目录中的所有JSON文件

        Args:
            repo: 实体仓库
            dir_path: 目录路径
            force: 是否强制覆盖已存在的数据

        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise ValueError(f"输入目录不存在: {dir_path}")

        files = [f for f in os.listdir(dir_path) if f.endswith(".json")]
        if not files:
            raise ValueError(f"目录中没有找到JSON文件: {dir_path}")

        imported = 0
        updated = 0
        skipped = 0

        for file_name in files:
            file_path = os.path.join(dir_path, file_name)
            try:
                result = self._restore_json_file(repo, file_path, force)
                imported += result.get("imported", 0)
                updated += result.get("updated", 0)
                skipped += result.get("skipped", 0)
            except Exception as e:
                self.logger.error(f"恢复文件失败: {file_path}, 错误: {str(e)}")

        result = {
            "entity_type": self.entity_type,
            "format": "json",
            "directory": dir_path,
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total": imported + updated + skipped,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"目录恢复结果: 导入={imported}, 更新={updated}, 跳过={skipped}")
        return result

    def _restore_from_sqlite(self, session: Session, input_path: str, force: bool = False) -> Dict[str, Any]:
        """
        从SQLite格式恢复实体

        Args:
            session: 数据库会话
            input_path: 输入路径
            force: 是否强制覆盖已存在的数据

        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        # 获取原始数据库路径
        db_path = get_db_path()

        # 如果现有数据库存在且没有强制覆盖标志，则抛出异常
        if os.path.exists(db_path) and not force:
            raise ValueError("数据库文件已存在。如果要覆盖现有数据库，请使用force=True")

        # 如果存在现有数据库，先创建备份
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            auto_backup = os.path.join(backup_dir, f"db_before_restore_{timestamp}.backup")
            shutil.copy2(db_path, auto_backup)
            self.logger.info(f"已创建现有数据库备份: {auto_backup}")

        # 复制备份文件到数据库位置
        shutil.copy2(input_path, db_path)

        result = {"entity_type": self.entity_type, "format": "sqlite", "input_path": input_path, "timestamp": datetime.now().isoformat()}

        self.logger.info(f"成功从 {input_path} 恢复数据库")
        return result


# 实体类型到处理器的映射
ENTITY_HANDLERS = {}


def register_entity_handler(entity_type: str, handler_class: Type[EntityBackupRestoreHandler]):
    """
    注册实体处理器

    Args:
        entity_type: 实体类型
        handler_class: 处理器类
    """
    ENTITY_HANDLERS[entity_type] = handler_class


def get_entity_handler(entity_type: str) -> Optional[Type[EntityBackupRestoreHandler]]:
    """
    获取实体处理器

    Args:
        entity_type: 实体类型

    Returns:
        Optional[Type[EntityBackupRestoreHandler]]: 处理器类
    """
    return ENTITY_HANDLERS.get(entity_type)


def backup_entity(session: Session, entity_type: str, output_path: str, format: str = "json") -> Dict[str, Any]:
    """
    备份指定类型的实体

    Args:
        session: 数据库会话
        entity_type: 实体类型
        output_path: 输出路径
        format: 输出格式

    Returns:
        Dict[str, Any]: 备份结果统计
    """
    handler_class = get_entity_handler(entity_type)

    if not handler_class:
        raise ValueError(f"未找到实体类型 {entity_type} 的处理器")

    handler = handler_class(entity_type)
    return handler.backup(session, output_path, format)


def restore_entity(session: Session, entity_type: str, input_path: str, format: str = "json", force: bool = False) -> Dict[str, Any]:
    """
    恢复指定类型的实体

    Args:
        session: 数据库会话
        entity_type: 实体类型
        input_path: 输入路径
        format: 输入格式
        force: 是否强制覆盖已存在的数据

    Returns:
        Dict[str, Any]: 恢复结果统计
    """
    handler_class = get_entity_handler(entity_type)

    if not handler_class:
        raise ValueError(f"未找到实体类型 {entity_type} 的处理器")

    handler = handler_class(entity_type)
    return handler.restore(session, input_path, format, force)


def backup_all_entities(session: Session, output_dir: str, format: str = "json") -> Dict[str, Any]:
    """
    备份所有实体

    Args:
        session: 数据库会话
        output_dir: 输出目录
        format: 输出格式

    Returns:
        Dict[str, Any]: 备份结果统计
    """
    results = {}

    for entity_type, handler_class in ENTITY_HANDLERS.items():
        try:
            entity_output_path = os.path.join(output_dir, entity_type)
            ensure_directory_exists(entity_output_path)

            handler = handler_class(entity_type)
            result = handler.backup(session, entity_output_path, format)
            results[entity_type] = result
        except Exception as e:
            logger.error(f"备份实体类型 {entity_type} 失败: {str(e)}")
            results[entity_type] = {"error": str(e)}

    return {
        "entity_types": list(ENTITY_HANDLERS.keys()),
        "format": format,
        "output_dir": output_dir,
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }


def restore_all_entities(session: Session, input_dir: str, format: str = "json", force: bool = False) -> Dict[str, Any]:
    """
    恢复所有实体

    Args:
        session: 数据库会话
        input_dir: 输入目录
        format: 输入格式
        force: 是否强制覆盖已存在的数据

    Returns:
        Dict[str, Any]: 恢复结果统计
    """
    results = {}

    for entity_type, handler_class in ENTITY_HANDLERS.items():
        try:
            entity_input_path = os.path.join(input_dir, entity_type)

            if not os.path.exists(entity_input_path):
                logger.warning(f"实体类型 {entity_type} 的输入路径不存在: {entity_input_path}")
                continue

            handler = handler_class(entity_type)
            result = handler.restore(session, entity_input_path, format, force)
            results[entity_type] = result
        except Exception as e:
            logger.error(f"恢复实体类型 {entity_type} 失败: {str(e)}")
            results[entity_type] = {"error": str(e)}

    return {
        "entity_types": list(ENTITY_HANDLERS.keys()),
        "format": format,
        "input_dir": input_dir,
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }
