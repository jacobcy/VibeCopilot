"""
数据库处理模块
提供数据库初始化和实体关系操作功能
"""

import json
import os
import sqlite3
from typing import Dict, List, Optional, Tuple


class DBHandler:
    """数据库处理类，提供Basic Memory数据库操作方法"""

    def __init__(self, db_path: str):
        """初始化数据库处理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = os.path.expanduser(db_path)
        self.setup_db()

    def setup_db(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 删除现有表
        c.execute("DROP TABLE IF EXISTS entities")
        c.execute("DROP TABLE IF EXISTS observations")
        c.execute("DROP TABLE IF EXISTS relations")

        # 创建新表
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

        conn.commit()
        conn.close()

    def create_entity(self, title: str, type_name: str = "note", metadata: Dict = None) -> int:
        """创建实体

        Args:
            title: 实体标题
            type_name: 实体类型
            metadata: 元数据

        Returns:
            int: 创建的实体ID
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None
        c.execute(
            "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
            (title, type_name, metadata_json),
        )
        entity_id = c.lastrowid

        conn.commit()
        conn.close()
        return entity_id

    def create_observation(self, entity_id: int, content: str, obs_type: str = "paragraph") -> None:
        """创建观察

        Args:
            entity_id: 实体ID
            content: 观察内容
            obs_type: 观察类型
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        metadata_json = json.dumps({"type": obs_type}) if obs_type != "paragraph" else None
        c.execute(
            "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
            (entity_id, content, metadata_json),
        )

        conn.commit()
        conn.close()

    def create_relation(self, source_id: int, target_id: int, relation_type: str, metadata: Dict = None) -> None:
        """创建关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            metadata: 元数据
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None
        c.execute(
            "INSERT INTO relations (source_id, target_id, type, metadata) VALUES (?, ?, ?, ?)",
            (source_id, target_id, relation_type, metadata_json),
        )

        conn.commit()
        conn.close()

    def get_entity_id(self, title: str) -> Optional[int]:
        """获取实体ID

        Args:
            title: 实体标题

        Returns:
            Optional[int]: 实体ID，如果不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id FROM entities WHERE title = ?", (title,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def get_entity_details(self, entity_id: int) -> Tuple[str, Dict, List[Tuple[str, str]], List[Tuple[str, str]]]:
        """获取实体详情

        Args:
            entity_id: 实体ID

        Returns:
            Tuple: (标题, 元数据, 观察列表, 关系列表)
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 获取实体信息
        c.execute("SELECT title, metadata FROM entities WHERE id = ?", (entity_id,))
        title, metadata_json = c.fetchone()
        metadata = json.loads(metadata_json) if metadata_json else {}

        # 获取观察
        c.execute(
            "SELECT content, metadata FROM observations WHERE entity_id = ? ORDER BY id",
            (entity_id,),
        )
        observations_raw = c.fetchall()
        observations = []
        for content, meta_json in observations_raw:
            meta = json.loads(meta_json) if meta_json else {}
            obs_type = meta.get("type", "paragraph")
            observations.append((content, obs_type))

        # 获取关系
        c.execute(
            """
            SELECT e.title, r.type
            FROM relations r
            JOIN entities e ON r.target_id = e.id
            WHERE r.source_id = ?
        """,
            (entity_id,),
        )
        relations = c.fetchall()

        conn.close()
        return title, metadata, observations, relations
