"""
Basic Memory数据库存储
管理存储和检索实体关系数据
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class MemoryStore:
    """Basic Memory数据库管理器"""

    def __init__(self, db_path: str):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path

    def setup_database(self) -> None:
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
        print(f"数据库初始化完成: {self.db_path}")

    def store_document(self, entity_data: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """存储文档和相关实体到数据库

        Args:
            entity_data: 实体关系数据
            file_path: 文件路径
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 处理文件路径
        if isinstance(file_path, Path):
            rel_path = str(file_path)
        else:
            rel_path = file_path

        # 1. 创建文档实体
        doc_metadata = {
            "document_type": entity_data.get("document_type", "unknown"),
            "main_topic": entity_data.get("main_topic", ""),
            "source_path": entity_data.get("source_path", rel_path),
            "tags": entity_data.get("tags", []),
        }

        document_title = None
        for entity in entity_data.get("entities", []):
            if entity.get("type") == "document":
                document_title = entity.get("name")
                break

        if not document_title:
            document_title = rel_path

        c.execute(
            "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
            (document_title, "document", json.dumps(doc_metadata)),
        )
        doc_id = c.lastrowid

        # 2. 存储原始内容作为观察
        original_content = ""
        for obs in entity_data.get("observations", []):
            original_content += obs + "\n\n"

        if original_content:
            c.execute(
                "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
                (doc_id, original_content, json.dumps({"type": "original_content"})),
            )

        # 3. 存储提取的观察
        for i, obs in enumerate(entity_data.get("observations", [])):
            c.execute(
                "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
                (doc_id, obs, json.dumps({"type": "extracted_observation", "order": i})),
            )

        # 4. 创建提取的实体
        entity_ids = {}  # 存储实体名称到ID的映射
        entity_ids[document_title] = doc_id  # 添加文档自身

        for entity in entity_data.get("entities", []):
            entity_name = entity.get("name", "")
            if not entity_name or entity_name == document_title:
                continue

            entity_metadata = {
                "type": entity.get("type", "concept"),
                "description": entity.get("description", ""),
                "source_document": document_title,
            }

            # 检查实体是否已存在
            c.execute("SELECT id FROM entities WHERE title = ?", (entity_name,))
            existing = c.fetchone()

            if existing:
                entity_ids[entity_name] = existing[0]
            else:
                c.execute(
                    "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
                    (entity_name, entity.get("type", "concept"), json.dumps(entity_metadata)),
                )
                entity_ids[entity_name] = c.lastrowid

        # 5. 创建关系
        for relation in entity_data.get("relations", []):
            source_name = relation.get("source", "")
            target_name = relation.get("target", "")
            rel_type = relation.get("type", "related_to")

            if not source_name or not target_name:
                continue

            # 如果源或目标不在ID映射中，检查是否需要创建
            if source_name not in entity_ids:
                c.execute("SELECT id FROM entities WHERE title = ?", (source_name,))
                existing = c.fetchone()

                if existing:
                    entity_ids[source_name] = existing[0]
                else:
                    # 创建为概念
                    c.execute(
                        "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
                        (source_name, "concept", json.dumps({"source_document": document_title})),
                    )
                    entity_ids[source_name] = c.lastrowid

            if target_name not in entity_ids:
                c.execute("SELECT id FROM entities WHERE title = ?", (target_name,))
                existing = c.fetchone()

                if existing:
                    entity_ids[target_name] = existing[0]
                else:
                    # 创建为概念
                    c.execute(
                        "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
                        (target_name, "concept", json.dumps({"source_document": document_title})),
                    )
                    entity_ids[target_name] = c.lastrowid

            # 创建关系
            c.execute(
                "INSERT INTO relations (source_id, target_id, type, metadata) VALUES (?, ?, ?, ?)",
                (
                    entity_ids[source_name],
                    entity_ids[target_name],
                    rel_type,
                    json.dumps({"source_document": document_title}),
                ),
            )

        conn.commit()
        conn.close()

    def print_stats(self) -> None:
        """打印数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 获取实体数量
        c.execute("SELECT COUNT(*) FROM entities")
        entity_count = c.fetchone()[0]

        # 获取观察数量
        c.execute("SELECT COUNT(*) FROM observations")
        observation_count = c.fetchone()[0]

        # 获取关系数量
        c.execute("SELECT COUNT(*) FROM relations")
        relation_count = c.fetchone()[0]

        # 获取实体类型统计
        c.execute("SELECT type, COUNT(*) FROM entities GROUP BY type")
        type_stats = c.fetchall()

        conn.close()

        print("\n数据库统计信息:")
        print(f"- 实体总数: {entity_count}")
        print(f"- 观察总数: {observation_count}")
        print(f"- 关系总数: {relation_count}")

        print("\n实体类型分布:")
        for type_name, count in type_stats:
            print(f"- {type_name}: {count}")

    def get_entity_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """根据标题获取实体

        Args:
            title: 实体标题

        Returns:
            Optional[Dict]: 实体信息，如果不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可按列名访问
        c = conn.cursor()

        # 查询实体
        c.execute("SELECT id, title, type, metadata FROM entities WHERE title = ?", (title,))
        row = c.fetchone()

        if not row:
            conn.close()
            return None

        entity_id = row["id"]
        entity_data = {
            "id": entity_id,
            "title": row["title"],
            "type": row["type"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        }

        # 获取实体的观察
        observations = []
        c.execute(
            "SELECT content, metadata FROM observations WHERE entity_id = ? ORDER BY id",
            (entity_id,),
        )
        for obs_row in c.fetchall():
            obs_metadata = json.loads(obs_row["metadata"]) if obs_row["metadata"] else {}
            observations.append({"content": obs_row["content"], "metadata": obs_metadata})

        entity_data["observations"] = observations

        # 获取实体的关系
        # 出向关系
        outgoing_relations = []
        c.execute(
            """
            SELECT r.id, r.target_id, r.type, r.metadata, e.title as target_title, e.type as target_type
            FROM relations r
            JOIN entities e ON r.target_id = e.id
            WHERE r.source_id = ?
            """,
            (entity_id,),
        )
        for rel_row in c.fetchall():
            rel_metadata = json.loads(rel_row["metadata"]) if rel_row["metadata"] else {}
            outgoing_relations.append(
                {
                    "id": rel_row["id"],
                    "target_id": rel_row["target_id"],
                    "target_title": rel_row["target_title"],
                    "target_type": rel_row["target_type"],
                    "type": rel_row["type"],
                    "metadata": rel_metadata,
                }
            )

        # 入向关系
        incoming_relations = []
        c.execute(
            """
            SELECT r.id, r.source_id, r.type, r.metadata, e.title as source_title, e.type as source_type
            FROM relations r
            JOIN entities e ON r.source_id = e.id
            WHERE r.target_id = ?
            """,
            (entity_id,),
        )
        for rel_row in c.fetchall():
            rel_metadata = json.loads(rel_row["metadata"]) if rel_row["metadata"] else {}
            incoming_relations.append(
                {
                    "id": rel_row["id"],
                    "source_id": rel_row["source_id"],
                    "source_title": rel_row["source_title"],
                    "source_type": rel_row["source_type"],
                    "type": rel_row["type"],
                    "metadata": rel_metadata,
                }
            )

        entity_data["outgoing_relations"] = outgoing_relations
        entity_data["incoming_relations"] = incoming_relations

        conn.close()
        return entity_data
