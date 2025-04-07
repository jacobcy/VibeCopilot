#!/usr/bin/env python3
"""
使用LangChain进行文档知识化并存储到Basic Memory
实现高级语义提取、向量化存储和检索功能
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 导入自定义模块
from adapters.basic_memory.db.memory_store import MemoryStore
from adapters.basic_memory.parsers.document_loader import DocumentLoader
from adapters.basic_memory.parsers.knowledge_extractor import KnowledgeExtractor
from adapters.basic_memory.parsers.vector_store import VectorManager
from adapters.basic_memory.utils.api_utils import get_openai_api_key


class LangChainKnowledgeProcessor:
    """使用LangChain进行文档知识化并存储到Basic Memory"""

    def __init__(self, source_dir: str, model: str = "gpt-4o-mini", db_path: Optional[str] = None):
        """初始化处理器

        Args:
            source_dir: 源文档目录
            model: 使用的OpenAI模型名称
            db_path: 数据库路径，如果未提供则使用默认路径
        """
        self.source_dir = Path(source_dir)
        self.model = model
        self.db_path = db_path or "/Users/chenyi/basic-memory/main.db"
        self.vector_index_path = "/Users/chenyi/basic-memory/vector_index"

        # 设置API密钥
        self.api_key = get_openai_api_key()
        if not self.api_key:
            print("错误: 无法获取OPENAI_API_KEY")
            sys.exit(1)

        # 初始化组件
        self.db = MemoryStore(self.db_path)
        self.document_loader = DocumentLoader(self.source_dir)
        self.knowledge_extractor = KnowledgeExtractor(self.model)
        self.vector_manager = VectorManager(self.vector_index_path, self.model)

        # 初始化数据库
        self.db.setup_database()

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
                self.db.store_vector_chunk(doc_entity_id, chunk_id, chunk, {"index": i, "doc_title": doc["title"]})

        # 创建向量存储
        if all_chunks:
            print(f"创建向量存储，处理 {len(all_chunks)} 个文本块...")
            vector_store = self.vector_manager.create_vector_store(all_chunks)
            self.vector_manager.save_vector_store(vector_store)
            print("向量存储创建完成")

        # 创建实体和关系
        self._process_chunks_for_entities(all_chunks, chunk_to_doc_map, document_entities)

        # 显示统计信息
        stats = self.db.get_database_stats()
        self._print_stats(stats, len(documents))

    def _process_chunks_for_entities(self, chunks: List[str], chunk_map: Dict, document_entities: Dict) -> None:
        """处理文档块，提取实体和关系

        Args:
            chunks: 文档块列表
            chunk_map: 块与文档的映射
            document_entities: 文档实体ID映射
        """
        print("开始提取知识...")

        # 创建文档标题到块的映射
        doc_chunks_map = {}
        for i, chunk in enumerate(chunks):
            doc_info = chunk_map.get(i)
            if doc_info:
                doc_title = doc_info["doc_title"]
                if doc_title not in doc_chunks_map:
                    doc_chunks_map[doc_title] = []
                doc_chunks_map[doc_title].append(chunk)

        # 提取知识
        documents = [{"title": title, "content": "".join(doc_chunks_map[title])} for title in doc_chunks_map]

        knowledge_results = self.knowledge_extractor.extract_batch(documents, doc_chunks_map)

        # 存储提取的知识
        for result in knowledge_results:
            doc_title = result.get("document_title")
            if not doc_title or doc_title not in document_entities:
                continue

            doc_entity_id = document_entities[doc_title]

            # 存储实体
            entity_ids = {}  # 存储实体名称到ID的映射
            entity_ids[doc_title] = doc_entity_id  # 添加文档自身

            for entity in result.get("entities", []):
                entity_name = entity.get("name")
                if not entity_name or entity_name == doc_title:
                    continue

                # 创建实体
                entity_id = self.db.create_entity(
                    entity_name,
                    entity.get("type", "concept"),
                    {"description": entity.get("description", ""), "source_document": doc_title},
                )
                entity_ids[entity_name] = entity_id

            # 存储关系
            for relation in result.get("relations", []):
                source = relation.get("source")
                target = relation.get("target")
                rel_type = relation.get("type", "related_to")

                if not source or not target:
                    continue

                if source in entity_ids and target in entity_ids:
                    self.db.create_relation(
                        entity_ids[source],
                        entity_ids[target],
                        rel_type,
                        {"source_document": doc_title},
                    )

            # 存储观察
            for i, obs in enumerate(result.get("observations", [])):
                self.db.create_observation(doc_entity_id, obs, {"type": "extracted_observation", "order": i})

    def _print_stats(self, stats: Dict, doc_count: int) -> None:
        """打印统计信息

        Args:
            stats: 数据库统计信息
            doc_count: 文档数量
        """
        print("\n处理完成！统计信息:")
        print(f"文档数量: {doc_count}")
        print(f"实体数量: {stats.get('entity_count', 0)}")
        print(f"关系数量: {stats.get('relation_count', 0)}")
        print(f"观察数量: {stats.get('observation_count', 0)}")
        print(f"向量块数量: {stats.get('vector_chunk_count', 0)}")
        print(f"数据库路径: {self.db_path}")
        print(f"向量索引路径: {self.vector_index_path}")


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
    print("1. 使用basic_memory export命令导出数据到Obsidian")
    print("2. 使用basic_memory query命令进行知识库问答")


if __name__ == "__main__":
    main()
