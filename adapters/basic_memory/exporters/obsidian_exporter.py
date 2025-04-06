"""
Obsidian导出模块
提供将实体关系数据导出到Obsidian格式的功能
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ObsidianExporter:
    """Obsidian导出器"""

    def __init__(self, output_dir: str):
        """初始化导出器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.entities_cache = {}  # 临时缓存实体

    def setup_output_dir(self) -> None:
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

    def export_all(self, memory_store) -> None:
        """导出所有实体

        Args:
            memory_store: 内存存储实例
        """
        # 获取并缓存所有实体
        conn = memory_store.db_path
        cursor = conn.cursor()

        # 加载所有实体ID和标题
        cursor.execute("SELECT id, title FROM entities")
        entities = cursor.fetchall()

        # 导出文档
        doc_count = 0
        concept_count = 0
        tag_count = 0

        for entity_id, title in entities:
            # 获取完整实体
            entity = memory_store.get_entity_by_title(title)
            if not entity:
                continue

            # 按类型导出
            if entity["type"] == "document":
                self.export_document(entity)
                doc_count += 1
            elif entity["type"] == "concept":
                self.export_concept(entity)
                concept_count += 1
            elif entity["type"] == "tag":
                self.export_tag(entity)
                tag_count += 1

        # 创建索引
        self.create_index()

        print(f"已导出 {doc_count} 个文档、{concept_count} 个概念和 {tag_count} 个标签")

    def export_document(self, entity: Dict[str, Any]) -> None:
        """导出文档实体到Markdown

        Args:
            entity: 实体数据
        """
        title = entity["title"]

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
            "entity_id": entity["id"],
            "entity_type": entity["type"],
        }

        # 添加原始元数据
        if entity["metadata"]:
            for key, value in entity["metadata"].items():
                if key not in front_matter:
                    front_matter[key] = value

        # 准备内容
        content_parts = []

        # 添加原始观察内容
        original_content = ""
        for observation in entity["observations"]:
            original_content += observation["content"] + "\n\n"

        content_parts.append(original_content.strip())

        # 添加关系部分 - 引用
        references = []
        for relation in entity.get("outgoing_relations", []):
            if relation["type"] == "references":
                references.append(f"- [[{relation['target_title']}]]")

        if references:
            content_parts.append("\n## 引用\n" + "\n".join(references))

        # 添加反向链接
        backlinks = []
        for relation in entity.get("incoming_relations", []):
            if relation["type"] == "references":
                backlinks.append(f"- [[{relation['source_title']}]]")

        if backlinks:
            content_parts.append("\n## 反向链接\n" + "\n".join(backlinks))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def export_concept(self, entity: Dict[str, Any]) -> None:
        """导出概念实体到Markdown

        Args:
            entity: 实体数据
        """
        title = entity["title"]
        output_path = self.output_dir / "concepts" / f"{title}.md"

        # 准备front matter
        front_matter = {
            "title": title,
            "entity_id": entity["id"],
            "entity_type": entity["type"],
            "created": datetime.now().isoformat(),
        }

        # 添加原始元数据
        if entity["metadata"]:
            for key, value in entity["metadata"].items():
                if key not in front_matter:
                    front_matter[key] = value

        # 准备内容
        content_parts = []

        # 添加描述
        description = entity["metadata"].get("description", f"关于 {title} 的概念")
        content_parts.append(f"# {title}\n\n{description}")

        # 添加原始观察
        if entity["observations"]:
            observations = []
            for observation in entity["observations"]:
                observations.append(observation["content"])

            if observations:
                content_parts.append("\n## 描述\n" + "\n\n".join(observations))

        # 添加关联文档
        doc_references = []
        for relation in entity.get("incoming_relations", []):
            if relation["type"] == "mentions" and relation["source_type"] in ["document", "note"]:
                doc_references.append(f"- [[{relation['source_title']}]]")

        if doc_references:
            content_parts.append("\n## 相关文档\n" + "\n".join(doc_references))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def export_tag(self, entity: Dict[str, Any]) -> None:
        """导出标签实体到Markdown

        Args:
            entity: 实体数据
        """
        title = entity["title"]
        output_path = self.output_dir / "tags" / f"{title}.md"

        # 准备front matter
        front_matter = {
            "title": title,
            "entity_id": entity["id"],
            "entity_type": "tag",
        }

        # 准备内容
        content_parts = []
        content_parts.append(f"# 标签: {title}")

        # 添加使用此标签的文档
        tagged_docs = []
        for relation in entity.get("incoming_relations", []):
            if relation["type"] == "tagged_with" and relation["source_type"] in [
                "document",
                "note",
            ]:
                tagged_docs.append(f"- [[{relation['source_title']}]]")

        if tagged_docs:
            content_parts.append("\n## 相关文档\n" + "\n".join(tagged_docs))

        # 生成最终内容
        front_matter_yaml = yaml.dump(front_matter, allow_unicode=True)
        final_content = f"---\n{front_matter_yaml}---\n\n" + "\n\n".join(content_parts)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def create_index(self) -> None:
        """创建索引文件"""
        # 查找已导出的文件
        docs = list(self.output_dir.glob("*.md"))
        docs.extend(self.output_dir.glob("*/*.md"))
        docs.extend(self.output_dir.glob("*/*/*.md"))

        # 按类型分类
        doc_files = [
            f
            for f in docs
            if f.parent == self.output_dir
            or not f.parent.name.startswith("concepts")
            and not f.parent.name.startswith("tags")
        ]
        concept_files = list(self.output_dir.glob("concepts/*.md"))
        tag_files = list(self.output_dir.glob("tags/*.md"))

        # 创建索引文件
        index_path = self.output_dir / "index.md"

        content = ["# Knowledge Base Index", ""]

        # 文档索引
        content.append("## Documents")
        for doc in sorted(doc_files, key=lambda x: x.name):
            rel_path = doc.relative_to(self.output_dir)
            content.append(f"- [[{rel_path}]]")

        # 概念索引
        content.append("\n## Concepts")
        for concept in sorted(concept_files, key=lambda x: x.name):
            name = concept.stem
            content.append(f"- [[concepts/{name}]]")

        # 标签索引
        content.append("\n## Tags")
        for tag in sorted(tag_files, key=lambda x: x.name):
            name = tag.stem
            content.append(f"- [[tags/{name}]]")

        # 写入文件
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"已创建索引文件: {index_path}")
