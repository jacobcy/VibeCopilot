#!/usr/bin/env python3
"""
从Basic Memory数据库导出到Obsidian
将实体关系数据转换为Obsidian友好的Markdown
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import yaml


class MemoryExporter:
    """从Basic Memory数据库导出到Obsidian的工具"""

    def __init__(self, db_path, output_dir):
        """初始化导出器

        Args:
            db_path: 数据库路径
            output_dir: 输出目录
        """
        self.db_path = os.path.expanduser(db_path)
        self.output_dir = Path(output_dir)
        self.entities_cache = {}  # 缓存实体信息
        self.relations_cache = {}  # 缓存关系信息

    def setup_output_dir(self):
        """设置输出目录"""
        if self.output_dir.exists():
            # 清理目录
            for item in self.output_dir.glob("**/*"):
                if item.is_file():
                    item.unlink()
        else:
            # 创建目录
            self.output_dir.mkdir(parents=True)

        # 创建子目录
        (self.output_dir / "entities").mkdir(exist_ok=True)
        (self.output_dir / "concepts").mkdir(exist_ok=True)
        (self.output_dir / "tags").mkdir(exist_ok=True)

    def load_data(self):
        """从数据库加载数据到缓存"""
        if not os.path.exists(self.db_path):
            print(f"错误: 数据库不存在: {self.db_path}")
            sys.exit(1)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可按列名访问
        cursor = conn.cursor()

        # 加载所有实体
        cursor.execute("SELECT id, title, type, metadata FROM entities")
        for row in cursor.fetchall():
            entity_id = row["id"]
            entity_data = {
                "id": entity_id,
                "title": row["title"],
                "type": row["type"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

            # 加载实体的观察
            observations = []
            cursor.execute(
                "SELECT content, metadata FROM observations WHERE entity_id = ? ORDER BY id",
                (entity_id,),
            )
            for obs_row in cursor.fetchall():
                obs_metadata = json.loads(obs_row["metadata"]) if obs_row["metadata"] else {}
                observations.append({"content": obs_row["content"], "metadata": obs_metadata})

            entity_data["observations"] = observations
            self.entities_cache[entity_id] = entity_data

        # 加载所有关系
        cursor.execute("SELECT id, source_id, target_id, type, metadata FROM relations")
        for row in cursor.fetchall():
            relation_id = row["id"]
            relation_data = {
                "id": relation_id,
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "type": row["type"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

            # 将关系添加到缓存
            self.relations_cache[relation_id] = relation_data

            # 更新实体的关系列表
            source_id = row["source_id"]
            if source_id in self.entities_cache:
                if "outgoing_relations" not in self.entities_cache[source_id]:
                    self.entities_cache[source_id]["outgoing_relations"] = []
                self.entities_cache[source_id]["outgoing_relations"].append(relation_data)

            target_id = row["target_id"]
            if target_id in self.entities_cache:
                if "incoming_relations" not in self.entities_cache[target_id]:
                    self.entities_cache[target_id]["incoming_relations"] = []
                self.entities_cache[target_id]["incoming_relations"].append(relation_data)

        conn.close()
        print(f"已加载 {len(self.entities_cache)} 个实体和 {len(self.relations_cache)} 个关系")

    def get_entity_by_title(self, title):
        """根据标题查找实体

        Args:
            title: 实体标题

        Returns:
            Dict: 实体数据，未找到返回None
        """
        for entity_id, entity_data in self.entities_cache.items():
            if entity_data["title"] == title:
                return entity_data
        return None

    def export_document_entities(self):
        """导出文档类型的实体"""
        docs_count = 0

        for entity_id, entity_data in self.entities_cache.items():
            if entity_data["type"] == "document" or entity_data["type"] == "note":
                self.export_document_entity(entity_data)
                docs_count += 1

        print(f"已导出 {docs_count} 个文档实体")

    def export_concept_entities(self):
        """导出概念类型的实体"""
        concepts_count = 0

        for entity_id, entity_data in self.entities_cache.items():
            if entity_data["type"] == "concept":
                self.export_concept_entity(entity_data)
                concepts_count += 1

        print(f"已导出 {concepts_count} 个概念实体")

    def export_tag_entities(self):
        """导出标签类型的实体"""
        tags_count = 0

        for entity_id, entity_data in self.entities_cache.items():
            if entity_data["type"] == "tag":
                self.export_tag_entity(entity_data)
                tags_count += 1

        print(f"已导出 {tags_count} 个标签实体")

    def export_document_entity(self, entity_data):
        """导出文档实体到Markdown

        Args:
            entity_data: 实体数据
        """
        title = entity_data["title"]

        # 对文档路径特殊处理，保持原有目录结构
        if "/" in title:
            path_parts = title.split("/")
            file_name = path_parts[-1]
            dir_path = "/".join(path_parts[:-1])

            target_dir = self.output_dir / dir_path
            target_dir.mkdir(parents=True, exist_ok=True)

            output_path = target_dir / file_name
        else:
            output_path = self.output_dir / title

        # 准备front matter
        front_matter = {
            "title": title,
            "entity_id": entity_data["id"],
            "entity_type": entity_data["type"],
        }

        # 添加原始元数据
        if entity_data["metadata"]:
            for key, value in entity_data["metadata"].items():
                if key not in front_matter:
                    front_matter[key] = value

        # 添加标签
        tags = []
        if "outgoing_relations" in entity_data:
            for relation in entity_data["outgoing_relations"]:
                if (
                    relation["type"] == "tagged_with"
                    and relation["target_id"] in self.entities_cache
                ):
                    tag_entity = self.entities_cache[relation["target_id"]]
                    tags.append(tag_entity["title"])

        if tags:
            front_matter["tags"] = tags

        # 准备内容
        content_parts = []

        # 添加原始观察内容
        original_content = ""
        for observation in entity_data["observations"]:
            original_content += observation["content"] + "\n\n"

        content_parts.append(original_content.strip())

        # 添加关系部分
        if "outgoing_relations" in entity_data and entity_data["outgoing_relations"]:
            references = []
            for relation in entity_data["outgoing_relations"]:
                if (
                    relation["type"] == "references"
                    and relation["target_id"] in self.entities_cache
                ):
                    target_entity = self.entities_cache[relation["target_id"]]
                    references.append(f"- [[{target_entity['title']}]]")

            if references:
                content_parts.append("\n## 引用\n" + "\n".join(references))

        if "incoming_relations" in entity_data and entity_data["incoming_relations"]:
            backlinks = []
            for relation in entity_data["incoming_relations"]:
                if (
                    relation["type"] == "references"
                    and relation["source_id"] in self.entities_cache
                ):
                    source_entity = self.entities_cache[relation["source_id"]]
                    backlinks.append(f"- [[{source_entity['title']}]]")

            if backlinks:
                content_parts.append("\n## 反向链接\n" + "\n".join(backlinks))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def export_concept_entity(self, entity_data):
        """导出概念实体到Markdown

        Args:
            entity_data: 实体数据
        """
        title = entity_data["title"]
        output_path = self.output_dir / "concepts" / f"{title}.md"

        # 准备front matter
        front_matter = {
            "title": title,
            "entity_id": entity_data["id"],
            "entity_type": entity_data["type"],
            "created": datetime.now().isoformat(),
        }

        # 添加原始元数据
        if entity_data["metadata"]:
            for key, value in entity_data["metadata"].items():
                if key not in front_matter:
                    front_matter[key] = value

        # 准备内容
        content_parts = []

        # 添加描述
        description = entity_data["metadata"].get("description", f"关于 {title} 的概念")
        content_parts.append(f"# {title}\n\n{description}")

        # 添加原始观察
        if entity_data["observations"]:
            observations = []
            for observation in entity_data["observations"]:
                observations.append(observation["content"])

            if observations:
                content_parts.append("\n## 描述\n" + "\n\n".join(observations))

        # 添加关联文档
        if "incoming_relations" in entity_data:
            doc_references = []
            for relation in entity_data["incoming_relations"]:
                if relation["type"] == "mentions" and relation["source_id"] in self.entities_cache:
                    doc_entity = self.entities_cache[relation["source_id"]]
                    if doc_entity["type"] in ["document", "note"]:
                        doc_references.append(f"- [[{doc_entity['title']}]]")

            if doc_references:
                content_parts.append("\n## 相关文档\n" + "\n".join(doc_references))

        # 添加相关概念
        related_concepts = []

        # 来自关系的相关概念
        if "outgoing_relations" in entity_data:
            for relation in entity_data["outgoing_relations"]:
                if relation["target_id"] in self.entities_cache:
                    target = self.entities_cache[relation["target_id"]]
                    if target["type"] == "concept":
                        related_concepts.append(f"- [[{target['title']}]] ({relation['type']})")

        if "incoming_relations" in entity_data:
            for relation in entity_data["incoming_relations"]:
                if relation["source_id"] in self.entities_cache:
                    source = self.entities_cache[relation["source_id"]]
                    if source["type"] == "concept":
                        related_concepts.append(f"- [[{source['title']}]] (被{relation['type']})")

        if related_concepts:
            content_parts.append("\n## 相关概念\n" + "\n".join(related_concepts))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def export_tag_entity(self, entity_data):
        """导出标签实体到Markdown

        Args:
            entity_data: 实体数据
        """
        title = entity_data["title"]
        output_path = self.output_dir / "tags" / f"{title}.md"

        # 准备front matter
        front_matter = {
            "title": title,
            "entity_id": entity_data["id"],
            "entity_type": "tag",
        }

        # 准备内容
        content_parts = []
        content_parts.append(f"# 标签: {title}")

        # 添加使用此标签的文档
        if "incoming_relations" in entity_data:
            tagged_docs = []
            for relation in entity_data["incoming_relations"]:
                if (
                    relation["type"] == "tagged_with"
                    and relation["source_id"] in self.entities_cache
                ):
                    doc_entity = self.entities_cache[relation["source_id"]]
                    if doc_entity["type"] in ["document", "note"]:
                        tagged_docs.append(f"- [[{doc_entity['title']}]]")

            if tagged_docs:
                content_parts.append("\n## 相关文档\n" + "\n".join(tagged_docs))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def create_index(self):
        """创建索引文件"""
        # 文档索引
        docs = []
        concepts = []
        tags = []

        for entity_id, entity_data in self.entities_cache.items():
            if entity_data["type"] in ["document", "note"]:
                docs.append(entity_data)
            elif entity_data["type"] == "concept":
                concepts.append(entity_data)
            elif entity_data["type"] == "tag":
                tags.append(entity_data)

        # 创建索引文件
        index_path = self.output_dir / "index.md"

        content = ["# Knowledge Base Index", ""]

        # 文档索引
        content.append("## Documents")
        for doc in sorted(docs, key=lambda x: x["title"]):
            content.append(f"- [[{doc['title']}]]")

        # 概念索引
        content.append("\n## Concepts")
        for concept in sorted(concepts, key=lambda x: x["title"]):
            content.append(f"- [[concepts/{concept['title']}]]")

        # 标签索引
        content.append("\n## Tags")
        for tag in sorted(tags, key=lambda x: x["title"]):
            content.append(f"- [[tags/{tag['title']}]]")

        # 写入文件
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"已创建索引文件: {index_path}")

    def export_all(self):
        """导出所有内容"""
        print(f"开始从 {self.db_path} 导出到 {self.output_dir}")

        self.setup_output_dir()
        self.load_data()

        self.export_document_entities()
        self.export_concept_entities()
        self.export_tag_entities()

        self.create_index()

        print(f"导出完成。数据已保存到: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description="从Basic Memory数据库导出到Obsidian")
    parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="Basic Memory数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )
    parser.add_argument(
        "--output",
        default="/Users/chenyi/basic-memory/obsidian_vault",
        help="Obsidian输出目录 (默认: /Users/chenyi/basic-memory/obsidian_vault)",
    )

    args = parser.parse_args()

    exporter = MemoryExporter(args.db, args.output)
    exporter.export_all()


if __name__ == "__main__":
    main()
