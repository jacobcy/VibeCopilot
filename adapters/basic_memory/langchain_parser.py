#!/usr/bin/env python3
"""
使用LangChain进行文档知识化并存储到Basic Memory
实现高级语义提取、向量化存储和检索功能
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 导入自定义模块
from scripts.basic_memory.lib.db_manager import BasicMemoryDB
from scripts.basic_memory.lib.document_loader import DocumentLoader
from scripts.basic_memory.lib.knowledge_extractor import KnowledgeExtractor
from scripts.basic_memory.lib.utils import get_openai_api_key
from scripts.basic_memory.lib.vector_store import VectorManager


class LangChainKnowledgeProcessor:
    """使用LangChain进行文档知识化并存储到Basic Memory"""

    def __init__(self, source_dir: str, model: str = "gpt-4o-mini"):
        """初始化处理器

        Args:
            source_dir: 源文档目录
            model: 使用的OpenAI模型名称
        """
        self.source_dir = Path(source_dir)
        self.model = model
        self.db_path = "/Users/chenyi/basic-memory/main.db"
        self.vector_index_path = "/Users/chenyi/basic-memory/vector_index"

        # 检查API密钥
        self.api_key = get_openai_api_key()
        if not self.api_key:
            print("错误: 无法获取OPENAI_API_KEY")
            sys.exit(1)

        # 初始化组件
        self.db = BasicMemoryDB(self.db_path)
        self.document_loader = DocumentLoader(self.source_dir)
        self.knowledge_extractor = KnowledgeExtractor(self.model)
        self.vector_manager = VectorManager(self.vector_index_path, self.model)

        # 初始化数据库
        self.db.setup_db()

    def process_documents(self) -> None:
        """处理文档，提取知识并存储"""
        print(f"开始处理目录: {self.source_dir}")

        # 加载文档
        documents = self.document_loader.load_documents()
        if not documents:
            print("警告: 没有找到文档")
            return

        print(f"已加载 {len(documents)} 个文档")

        # 创建向量存储
        all_chunks = []
        chunk_to_doc_map = {}  # 用于记录块与文档的关系

        # 创建所有文档实体
        document_entities = {}
        for doc in documents:
            # 创建文档实体
            doc_metadata = {
                "source_path": doc["title"],
                "imported_at": datetime.now().isoformat(),
                **doc.get("metadata", {}),
            }

            doc_entity_id = self.db.create_entity(doc["title"], "document", doc_metadata)
            document_entities[doc["title"]] = doc_entity_id

            # 存储原始内容
            self.db.create_observation(doc_entity_id, doc["content"], {"type": "original_content"})

            # 分割文档
            chunks = self.document_loader.split_document(doc["content"])

            # 为每个块创建唯一ID并记录关系
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['title']}_{i}"
                all_chunks.append(chunk)
                chunk_to_doc_map[len(all_chunks) - 1] = {
                    "doc_title": doc["title"],
                    "chunk_id": chunk_id,
                    "entity_id": doc_entity_id,
                }

                # 存储块到向量块表
                self.db.store_vector_chunk(
                    doc_entity_id, chunk_id, chunk, {"index": i, "doc_title": doc["title"]}
                )

        # 创建向量存储
        if all_chunks:
            vector_store = self.vector_manager.create_vector_store(all_chunks)
            self.vector_manager.save_vector_store(vector_store)

        # 创建实体和关系
        self._process_chunks_for_entities(all_chunks, chunk_to_doc_map, document_entities)

        # 显示统计信息
        stats = self.db.get_database_stats()
        self._print_stats(stats, len(documents))

    def _process_chunks_for_entities(self, all_chunks, chunk_to_doc_map, document_entities):
        """处理文本块以提取实体和关系"""
        print("开始提取实体和关系...")

        # 创建实体ID映射
        entity_ids = {}  # 实体名称到ID的映射

        # 处理每个文本块
        for i, chunk in enumerate(all_chunks):
            if i % 10 == 0:
                print(f"正在处理第 {i+1}/{len(all_chunks)} 个文本块...")

            doc_info = chunk_to_doc_map[i]
            doc_title = doc_info["doc_title"]
            doc_entity_id = doc_info["entity_id"]

            # 提取实体和关系
            result = self.knowledge_extractor.extract_entities_and_relations(chunk, doc_title)

            # 更新文档元数据
            self._update_document_metadata(i, result, doc_entity_id)

            # 处理实体
            self._process_entities(
                result.get("entities", []), entity_ids, doc_title, doc_info, doc_entity_id
            )

            # 处理关系
            self._process_relations(result.get("relations", []), entity_ids, doc_title, doc_info)

            # 处理观察
            self._process_observations(result.get("observations", []), doc_entity_id, doc_info)

            # 处理标签
            self._process_tags(result.get("tags", []), doc_title, doc_entity_id)

    def _update_document_metadata(self, index, result, doc_entity_id):
        """更新文档元数据"""
        if index == 0 and (result.get("document_type") or result.get("main_topic")):
            metadata_updates = {}

            if result.get("document_type"):
                metadata_updates["document_type"] = result["document_type"]
            if result.get("main_topic"):
                metadata_updates["main_topic"] = result["main_topic"]
            if result.get("tags"):
                metadata_updates["tags"] = result["tags"]

            self.db.update_entity_metadata(doc_entity_id, metadata_updates)

    def _process_entities(self, entities, entity_ids, doc_title, doc_info, doc_entity_id):
        """处理实体"""
        for entity in entities:
            entity_name = entity.get("name", "").strip()
            if not entity_name:
                continue

            # 检查实体是否已存在
            if entity_name in entity_ids:
                continue

            # 创建新实体
            entity_type = entity.get("type", "concept").strip() or "concept"
            entity_metadata = {
                "description": entity.get("description", ""),
                "source_document": doc_title,
                "chunk_id": doc_info["chunk_id"],
            }

            entity_id = self.db.create_entity(entity_name, entity_type, entity_metadata)
            entity_ids[entity_name] = entity_id

            # 创建实体与文档的关系
            self.db.create_relation(
                doc_entity_id, entity_id, "contains", {"chunk_id": doc_info["chunk_id"]}
            )

    def _process_relations(self, relations, entity_ids, doc_title, doc_info):
        """处理关系"""
        for relation in relations:
            source_name = relation.get("source", "").strip()
            target_name = relation.get("target", "").strip()
            relation_type = relation.get("type", "").strip()

            if not source_name or not target_name or not relation_type:
                continue

            # 确保源实体和目标实体存在
            if source_name not in entity_ids:
                source_metadata = {
                    "description": f"从关系提取的实体：{relation_type}关系的源",
                    "source_document": doc_title,
                    "auto_generated": True,
                }
                source_id = self.db.create_entity(source_name, "concept", source_metadata)
                entity_ids[source_name] = source_id
            else:
                source_id = entity_ids[source_name]

            if target_name not in entity_ids:
                target_metadata = {
                    "description": f"从关系提取的实体：{relation_type}关系的目标",
                    "source_document": doc_title,
                    "auto_generated": True,
                }
                target_id = self.db.create_entity(target_name, "concept", target_metadata)
                entity_ids[target_name] = target_id
            else:
                target_id = entity_ids[target_name]

            # 创建关系
            relation_metadata = {
                "description": relation.get("description", ""),
                "source_document": doc_title,
                "chunk_id": doc_info["chunk_id"],
            }

            self.db.create_relation(source_id, target_id, relation_type, relation_metadata)

    def _process_observations(self, observations, doc_entity_id, doc_info):
        """处理观察"""
        for idx, obs in enumerate(observations):
            if not obs.strip():
                continue

            self.db.create_observation(
                doc_entity_id,
                obs,
                {
                    "type": "extracted_observation",
                    "order": idx,
                    "chunk_id": doc_info["chunk_id"],
                },
            )

    def _process_tags(self, tags, doc_title, doc_entity_id):
        """处理标签"""
        if tags is None:
            tags = []

        for tag in tags:
            tag_name = tag.strip()
            if not tag_name:
                continue

            # 检查标签是否已存在
            tag_id = self.db.get_entity_id(tag_name)
            if not tag_id:
                tag_id = self.db.create_entity(tag_name, "tag", {"source_document": doc_title})

            # 创建文档与标签的关系
            self.db.create_relation(doc_entity_id, tag_id, "tagged_with")

    def _print_stats(self, stats, doc_count):
        """打印处理统计信息"""
        print(f"\n导入完成! 共处理了 {doc_count} 个文件。")
        print(f"数据已存储到: {self.db_path}")
        print(f"向量索引已保存到: {self.vector_index_path}")

        print("\n数据库统计信息:")
        print(f"- 实体总数: {stats['entity_count']}")
        print(f"- 观察总数: {stats['observation_count']}")
        print(f"- 关系总数: {stats['relation_count']}")
        print(f"- 向量块总数: {stats['vector_chunk_count']}")

        print("\n实体类型分布:")
        for type_name, count in stats["entity_types"].items():
            print(f"- {type_name}: {count}")

    def create_query_interface(self):
        """创建查询接口

        Returns:
            ConversationalRetrievalChain: 查询链
        """
        return self.vector_manager.create_query_interface()


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python langchain_parser.py <source_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    if not os.path.isdir(source_dir):
        print(f"错误: 目录不存在: {source_dir}")
        sys.exit(1)

    # 显示信息
    print(f"使用LangChain处理目录: {source_dir}")
    print("----------------------------")
    print("执行操作:")
    print("1. 清空现有Basic Memory数据库")
    print("2. 加载并分割文档")
    print("3. 创建向量嵌入和索引")
    print("4. 提取知识实体和关系")
    print("5. 构建知识图谱")
    print("----------------------------")

    # 创建处理器并处理文档
    processor = LangChainKnowledgeProcessor(source_dir)
    processor.process_documents()

    print("\n处理完成! 您可以:")
    print("1. 使用export_to_obsidian.py导出数据到Obsidian")
    print("2. 使用query_knowledge.py进行知识库问答")


if __name__ == "__main__":
    main()
