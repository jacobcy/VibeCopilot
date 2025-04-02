#!/usr/bin/env python3
"""
数据库管理模块，负责Basic Memory数据的存储和检索
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BasicMemoryDB:
    """Basic Memory数据库管理类"""

    def __init__(self, db_path: str):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.ensure_db_dir()

    def ensure_db_dir(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def setup_db(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 删除现有表
        c.execute("DROP TABLE IF EXISTS entities")
        c.execute("DROP TABLE IF EXISTS observations")
        c.execute("DROP TABLE IF EXISTS relations")
        c.execute("DROP TABLE IF EXISTS vector_chunks")

        # 创建基本表
        c.execute(
            """
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            metadata TEXT
        )"""
        )

        c.execute(
            """
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER,
            content TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )"""
        )

        c.execute(
            """
        CREATE TABLE relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            target_id INTEGER,
            type TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (source_id) REFERENCES entities (id),
            FOREIGN KEY (target_id) REFERENCES entities (id)
        )"""
        )

        # 创建向量块表
        c.execute(
            """
        CREATE TABLE vector_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER,
            chunk_id TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )"""
        )

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def create_entity(self, title: str, type_name: str, metadata: Dict = None) -> int:
        """创建实体

        Args:
            title: 实体标题
            type_name: 实体类型
            metadata: 元数据

        Returns:
            int: 实体ID
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
            (title, type_name, json.dumps(metadata or {})),
        )

        entity_id = c.lastrowid
        conn.commit()
        conn.close()

        return entity_id

    def create_observation(self, entity_id: int, content: str, metadata: Dict = None) -> int:
        """创建观察

        Args:
            entity_id: 实体ID
            content: 观察内容
            metadata: 元数据

        Returns:
            int: 观察ID
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
            (entity_id, content, json.dumps(metadata or {})),
        )

        observation_id = c.lastrowid
        conn.commit()
        conn.close()

        return observation_id

    def create_relation(
        self, source_id: int, target_id: int, relation_type: str, metadata: Dict = None
    ) -> int:
        """创建关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            metadata: 元数据

        Returns:
            int: 关系ID
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "INSERT INTO relations (source_id, target_id, type, metadata) VALUES (?, ?, ?, ?)",
            (source_id, target_id, relation_type, json.dumps(metadata or {})),
        )

        relation_id = c.lastrowid
        conn.commit()
        conn.close()

        return relation_id

    def get_entity_id(self, title: str) -> Optional[int]:
        """获取实体ID

        Args:
            title: 实体标题

        Returns:
            Optional[int]: 实体ID，不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT id FROM entities WHERE title = ?", (title,))
        result = c.fetchone()

        conn.close()

        return result[0] if result else None

    def store_vector_chunk(
        self, entity_id: int, chunk_id: str, content: str, metadata: Dict = None
    ) -> int:
        """存储向量块

        Args:
            entity_id: 实体ID
            chunk_id: 块ID
            content: 块内容
            metadata: 元数据

        Returns:
            int: 向量块ID
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "INSERT INTO vector_chunks (entity_id, chunk_id, content, metadata) VALUES (?, ?, ?, ?)",
            (entity_id, chunk_id, content, json.dumps(metadata or {})),
        )

        chunk_id = c.lastrowid
        conn.commit()
        conn.close()

        return chunk_id

    def update_entity_metadata(self, entity_id: int, metadata_updates: Dict) -> bool:
        """更新实体元数据

        Args:
            entity_id: 实体ID
            metadata_updates: 要更新的元数据

        Returns:
            bool: 是否更新成功
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            c.execute("SELECT metadata FROM entities WHERE id = ?", (entity_id,))
            metadata_str = c.fetchone()[0]
            metadata = json.loads(metadata_str)

            # 更新元数据
            metadata.update(metadata_updates)

            c.execute(
                "UPDATE entities SET metadata = ? WHERE id = ?",
                (json.dumps(metadata), entity_id),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新实体元数据失败: {e}")
            conn.close()
            return False

    def get_database_stats(self) -> Dict:
        """获取数据库统计信息

        Returns:
            Dict: 统计信息
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        stats = {}

        c.execute("SELECT COUNT(*) FROM entities")
        stats["entity_count"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM observations")
        stats["observation_count"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM relations")
        stats["relation_count"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM vector_chunks")
        stats["vector_chunk_count"] = c.fetchone()[0]

        c.execute("SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC")
        stats["entity_types"] = {type_name: count for type_name, count in c.fetchall()}

        conn.close()

        return stats
