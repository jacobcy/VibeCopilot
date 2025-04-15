#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新MemoryItem表结构
添加向量库相关字段
"""

import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from sqlalchemy import Column, DateTime, Integer, String, create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.db.connection_manager import get_engine, get_session
from src.models.db import Base
from src.models.db.init_db import get_db_path
from src.models.db.memory_item import MemoryItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def add_column(engine, table_name, column):
    """添加列到表

    Args:
        engine: SQLAlchemy引擎
        table_name: 表名
        column: 列对象
    """
    column_name = column.name
    column_type = column.type.compile(engine.dialect)
    try:
        engine.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        logger.info(f"添加列 {column_name} 到表 {table_name}")
    except Exception as e:
        logger.warning(f"添加列 {column_name} 失败: {e}")


def update_memory_item_schema():
    """更新MemoryItem表结构"""
    logger.info("开始更新MemoryItem表结构...")

    # 获取数据库引擎
    engine = get_engine()

    # 获取表结构检查器
    inspector = inspect(engine)

    # 检查表是否存在
    if "memory_items" not in inspector.get_table_names():
        logger.error("memory_items表不存在，请先初始化数据库")
        return False

    # 获取现有列
    columns = [column["name"] for column in inspector.get_columns("memory_items")]
    logger.info(f"现有列: {columns}")

    # 定义需要添加的列
    new_columns = []
    if "permalink" not in columns:
        new_columns.append(Column("permalink", String(255)))
    if "folder" not in columns:
        new_columns.append(Column("folder", String(100)))
    if "entity_count" not in columns:
        new_columns.append(Column("entity_count", Integer, default=0))
    if "relation_count" not in columns:
        new_columns.append(Column("relation_count", Integer, default=0))
    if "observation_count" not in columns:
        new_columns.append(Column("observation_count", Integer, default=0))
    if "vector_updated_at" not in columns:
        new_columns.append(Column("vector_updated_at", DateTime, nullable=True))

    # 添加列
    for column in new_columns:
        add_column(engine, "memory_items", column)

    logger.info("更新MemoryItem表结构完成")
    return True


if __name__ == "__main__":
    try:
        success = update_memory_item_schema()
        if success:
            print("成功更新MemoryItem表结构")
        else:
            print("更新MemoryItem表结构失败")
    except Exception as e:
        logger.error(f"更新过程中发生错误: {e}", exc_info=True)
        print(f"更新失败: {e}")
