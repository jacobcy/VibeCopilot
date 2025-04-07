"""
文档导入器主模块
整合其他模块功能，实现文档导入和导出
"""

import os
from pathlib import Path
from typing import Dict

from .db_handler import DBHandler
from .markdown_parser import MarkdownParser
from .obsidian_exporter import ObsidianExporter


class DocImporter:
    """文档导入器，将Markdown文档导入到Basic Memory并导出到Obsidian"""

    def __init__(self, source_dir: str):
        """初始化导入器

        Args:
            source_dir: 源文档目录
        """
        self.source_dir = Path(source_dir)
        self.db_path = "/Users/chenyi/basic-memory/main.db"
        self.vault_path = "/Users/chenyi/basic-memory/vault"

        # 初始化组件
        self.db = DBHandler(self.db_path)
        self.exporter = ObsidianExporter(self.vault_path)

    def import_docs(self) -> None:
        """导入文档"""
        print(f"开始导入文档: {self.source_dir}")

        # 第一遍：创建所有实体
        entities = {}
        for md_file in self.source_dir.rglob("*.md"):
            try:
                print(f"处理文件: {md_file}")

                # 读取文件内容
                content = md_file.read_text(encoding="utf-8")

                # 解析文档
                metadata, content = MarkdownParser.extract_front_matter(content)
                observations = MarkdownParser.split_content(content)

                # 使用相对路径作为标题
                title = str(md_file.relative_to(self.source_dir))

                # 创建实体
                entity_id = self.db.create_entity(title, "note", metadata)
                entities[title] = {
                    "id": entity_id,
                    "content": content,
                    "metadata": metadata,
                    "file_path": md_file,
                    "observations": observations,
                }

                # 创建观察
                for obs in observations:
                    self.db.create_observation(entity_id, obs["content"], obs["type"])

            except Exception as e:
                print(f"警告: 处理文件 {md_file} 时出错: {str(e)}")
                continue

        # 第二遍：建立关系并导出
        for title, entity in entities.items():
            try:
                # 提取链接
                links = MarkdownParser.extract_links(entity["content"])

                # 创建引用关系
                for link in links:
                    target_id = self.db.get_entity_id(link)
                    if target_id:
                        self.db.create_relation(entity["id"], target_id, "references")

                # 处理标签
                tags = MarkdownParser.extract_tags(entity["content"], entity["metadata"])
                for tag in tags:
                    tag_id = self.db.get_entity_id(tag)
                    if not tag_id:
                        tag_id = self.db.create_entity(tag, "tag")
                    self.db.create_relation(entity["id"], tag_id, "tagged_with")

                # 导出到Obsidian
                entity_details = self.db.get_entity_details(entity["id"])
                _, metadata, observations, relations = entity_details
                self.exporter.export_document(entity["file_path"], self.source_dir, metadata, observations, relations)

            except Exception as e:
                print(f"警告: 处理关系时出错: {str(e)}")
                continue

        print(f"导入完成。处理了 {len(entities)} 个文件。")
        print(f"文档已导出到: {os.path.expanduser(self.vault_path)}")
