#!/usr/bin/env python3
"""
OpenAI内存解析器
用于使用OpenAI API解析文档，提取实体和关系，并存储到Basic Memory数据库中
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

from scripts.basic_memory.lib.db_manager import MemoryDBManager
from scripts.basic_memory.lib.document_loader import DocumentLoader
from scripts.basic_memory.lib.openai_api import OpenAIClient


class OpenAIMemoryParser:
    """使用OpenAI API解析文档，提取实体和关系，并存储到Basic Memory数据库中"""

    def __init__(self, source_dir, model="gpt-4o-mini"):
        """
        初始化解析器

        Args:
            source_dir (str): 源文档目录
            model (str): 使用的OpenAI模型
        """
        self.source_dir = source_dir
        self.db_path = os.path.join(os.path.dirname(source_dir), "memory.db")

        # 加载文档
        self.document_loader = DocumentLoader(source_dir)

        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient(model)

        # 设置数据库
        self.db_manager = MemoryDBManager(self.db_path)
        self.db_manager.setup_db()

        # 处理计数
        self.processed_count = 0
        self.total_files = 0

        print(f"Initialized OpenAI Memory Parser with model: {model}")
        print(f"Source directory: {source_dir}")
        print(f"Database path: {self.db_path}")

    def _store_parse_result(self, result, file_path, content):
        """
        将解析结果存储到数据库

        Args:
            result (dict): 解析结果
            file_path (str): 文件路径
            content (str): 文件内容
        """
        # 获取相对路径作为文档ID
        rel_path = os.path.relpath(file_path, self.source_dir)
        doc_id = rel_path.replace("\\", "/")

        # 存储实体
        for entity in result.get("entities", []):
            entity_name = entity.get("name", "").strip()
            entity_type = entity.get("type", "Concept").strip()
            description = entity.get("description", "").strip()

            if not entity_name:
                continue

            # 存储实体
            self.db_manager.add_entity(entity_name, entity_type, description, doc_id)

        # 存储关系
        for relation in result.get("relationships", []):
            source = relation.get("source", "").strip()
            target = relation.get("target", "").strip()
            rel_type = relation.get("type", "Related").strip()
            description = relation.get("description", "").strip()

            if not source or not target:
                continue

            # 存储关系
            self.db_manager.add_relation(source, target, rel_type, description, doc_id)

        # 存储文档
        title = os.path.basename(file_path)
        if title.endswith((".md", ".txt")):
            title = os.path.splitext(title)[0]

        self.db_manager.add_document(doc_id, title, content, len(content))

        # 存储文档实体关系
        stored_entities = {e.get("name") for e in result.get("entities", [])}

        for entity_name in stored_entities:
            if entity_name:
                self.db_manager.add_doc_entity(doc_id, entity_name)

    def process_documents(self):
        """处理所有文档，提取信息并存储到数据库"""
        documents = self.document_loader.load_documents()
        self.total_files = len(documents)

        print(f"Found {self.total_files} documents to process")

        if self.total_files == 0:
            print("No documents found. Exiting.")
            return

        for i, (file_path, content) in enumerate(documents):
            if not content.strip():
                print(f"Skipping empty file: {file_path}")
                continue

            print(f"Processing [{i+1}/{self.total_files}]: {file_path}")

            try:
                # 使用OpenAI解析内容
                result = self.openai_client.parse_content(content, file_path)

                # 存储结果
                self._store_parse_result(result, file_path, content)

                self.processed_count += 1
                print(
                    f"  Extracted {len(result.get('entities', []))} entities, "
                    f"{len(result.get('relationships', []))} relationships"
                )

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue

        print(
            f"\nProcessing complete. Processed {self.processed_count} of {self.total_files} files."
        )
        self._print_stats()

    def _print_stats(self):
        """打印数据库统计信息"""
        stats = self.db_manager.get_stats()

        print("\nDatabase Statistics:")
        print(f"  Documents: {stats['document_count']}")
        print(f"  Entities: {stats['entity_count']}")
        print(f"  Relations: {stats['relation_count']}")
        print(f"  Doc-Entity Links: {stats['doc_entity_count']}")

        # 打印实体类型分布
        if stats["entity_types"]:
            print("\nEntity Types:")
            for entity_type, count in stats["entity_types"].items():
                print(f"  {entity_type}: {count}")

        # 打印关系类型分布
        if stats["relation_types"]:
            print("\nRelation Types:")
            for relation_type, count in stats["relation_types"].items():
                print(f"  {relation_type}: {count}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python openai_parser.py <source_directory> [model_name]")
        sys.exit(1)

    source_dir = sys.argv[1]
    model = "gpt-4o-mini"  # 默认模型

    if len(sys.argv) > 2:
        model = sys.argv[2]

    parser = OpenAIMemoryParser(source_dir, model)
    parser.process_documents()


if __name__ == "__main__":
    main()
