#!/usr/bin/env python3
"""
使用LangChain进行文档知识化并存储到Basic Memory
实现高级语义提取、向量化存储和检索功能
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import frontmatter
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter

# LangChain导入
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field


def extract_api_key_from_env_file(env_path=".env"):
    """从.env文件中提取API密钥

    Args:
        env_path: .env文件路径

    Returns:
        str: API密钥
    """
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.strip().startswith("OPENAI_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip()
                    # 去掉可能的引号
                    key = key.strip('"').strip("'")
                    return key
    except Exception as e:
        print(f"读取.env文件失败: {e}")
    return None


class LangChainKnowledgeProcessor:
    """使用LangChain进行文档知识化并存储到Basic Memory"""

    def __init__(self, source_dir: str, model: str = "gpt-3.5-turbo-0125"):
        """初始化处理器

        Args:
            source_dir: 源文档目录
            model: 使用的OpenAI模型名称
        """
        self.source_dir = Path(source_dir)
        self.model = model
        self.db_path = "/Users/chenyi/basic-memory/main.db"
        self.vector_index_path = "/Users/chenyi/basic-memory/vector_index"

        # 从.env文件获取API密钥
        self.api_key = extract_api_key_from_env_file()
        if not self.api_key:
            print("错误: 无法从.env文件中提取OPENAI_API_KEY")
            sys.exit(1)

        # 初始化OpenAI模型
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        self.llm = ChatOpenAI(model=self.model, temperature=0.2, streaming=False, verbose=False)

        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings()

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n#### ", "\n", " ", ""],
            keep_separator=True,
        )

        # 初始化数据库
        self._setup_db()

    def _setup_db(self) -> None:
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

    def load_documents(self) -> List[Dict[str, Any]]:
        """加载文档并解析前置元数据

        Returns:
            List[Dict]: 文档内容和元数据列表
        """
        documents = []

        # 遍历所有Markdown文件
        for md_file in self.source_dir.rglob("*.md"):
            try:
                # 读取文件内容
                content = md_file.read_text(encoding="utf-8")

                # 解析前置元数据
                post = frontmatter.loads(content)
                metadata = post.metadata
                content_text = post.content

                # 使用相对路径作为标题
                rel_path = str(md_file.relative_to(self.source_dir))

                documents.append(
                    {
                        "title": rel_path,
                        "content": content_text,
                        "metadata": metadata,
                        "file_path": md_file,
                    }
                )

                print(f"已加载: {rel_path}")

            except Exception as e:
                print(f"警告: 处理文件 {md_file} 时出错: {str(e)}")
                continue

        return documents

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

    def extract_entities_and_relations(self, chunk_text: str, doc_title: str) -> Dict:
        """使用LLM提取实体和关系

        Args:
            chunk_text: 文本块内容
            doc_title: 文档标题

        Returns:
            Dict: 包含提取结果的字典
        """

        # 定义提取模式
        class Entity(BaseModel):
            name: str = Field(description="实体名称")
            type: str = Field(description="实体类型")
            description: Optional[str] = Field(description="实体描述")

        class Relation(BaseModel):
            source: str = Field(description="关系源实体")
            target: str = Field(description="关系目标实体")
            type: str = Field(description="关系类型")
            description: Optional[str] = Field(description="关系描述")

        class ExtractionResult(BaseModel):
            document_type: Optional[str] = Field(description="文档类型")
            main_topic: Optional[str] = Field(description="主要主题")
            entities: List[Entity] = Field(description="提取的实体列表")
            relations: List[Relation] = Field(description="提取的关系列表")
            observations: List[str] = Field(description="关键观察点列表")
            tags: Optional[List[str]] = Field(description="标签列表")

        # 创建结构化输出模型
        structured_llm = self.llm.with_structured_output(ExtractionResult)

        # 构建提示
        prompt = f"""分析以下文本片段，提取主要实体和关系。

文档标题: {doc_title}

文本内容:
{chunk_text}

请提取:
1. 文档类型和主题
2. 所有重要的实体、概念、组件
3. 实体之间的关系
4. 关键的观察点和见解
5. 相关标签

注意:
- 只提取确实存在于文本中的实体和关系
- 实体名称应简洁明确
- 关系必须有明确的源和目标
"""

        try:
            # 执行提取
            result = structured_llm.invoke(prompt)

            # 将结果转换为字典
            result_dict = result.model_dump()

            return result_dict
        except Exception as e:
            print(f"提取实体和关系时出错: {e}")
            return {
                "document_type": "unknown",
                "main_topic": doc_title,
                "entities": [],
                "relations": [],
                "observations": ["文本内容无法解析"],
                "tags": [],
            }

    def process_documents(self) -> None:
        """处理文档，提取知识并存储"""
        print(f"开始处理目录: {self.source_dir}")

        # 加载文档
        documents = self.load_documents()
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

            doc_entity_id = self.create_entity(doc["title"], "document", doc_metadata)
            document_entities[doc["title"]] = doc_entity_id

            # 存储原始内容
            self.create_observation(doc_entity_id, doc["content"], {"type": "original_content"})

            # 分割文档
            chunks = self.text_splitter.split_text(doc["content"])

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
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO vector_chunks (entity_id, chunk_id, content, metadata) VALUES (?, ?, ?, ?)",
                    (
                        doc_entity_id,
                        chunk_id,
                        chunk,
                        json.dumps({"index": i, "doc_title": doc["title"]}),
                    ),
                )
                conn.commit()
                conn.close()

        # 创建向量存储
        if all_chunks:
            print(f"创建向量索引，共 {len(all_chunks)} 个文本块")
            vector_store = FAISS.from_texts(all_chunks, self.embeddings)

            # 保存向量索引
            os.makedirs(os.path.dirname(self.vector_index_path), exist_ok=True)
            vector_store.save_local(self.vector_index_path)
            print(f"向量索引已保存到: {self.vector_index_path}")

        # 提取实体和关系
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
            result = self.extract_entities_and_relations(chunk, doc_title)

            # 更新文档元数据
            if i == 0 and (result.get("document_type") or result.get("main_topic")):
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT metadata FROM entities WHERE id = ?", (doc_entity_id,))
                metadata_str = c.fetchone()[0]
                metadata = json.loads(metadata_str)

                if result.get("document_type"):
                    metadata["document_type"] = result["document_type"]
                if result.get("main_topic"):
                    metadata["main_topic"] = result["main_topic"]
                if result.get("tags"):
                    metadata["tags"] = result["tags"]

                c.execute(
                    "UPDATE entities SET metadata = ? WHERE id = ?",
                    (json.dumps(metadata), doc_entity_id),
                )
                conn.commit()
                conn.close()

            # 创建实体
            for entity in result.get("entities", []):
                entity_name = entity.get("name", "").strip()
                if not entity_name:
                    continue

                # 检查实体是否已存在
                if entity_name in entity_ids:
                    # 更新实体描述
                    continue

                # 创建新实体
                entity_type = entity.get("type", "concept").strip() or "concept"
                entity_metadata = {
                    "description": entity.get("description", ""),
                    "source_document": doc_title,
                    "chunk_id": doc_info["chunk_id"],
                }

                entity_id = self.create_entity(entity_name, entity_type, entity_metadata)
                entity_ids[entity_name] = entity_id

                # 创建实体与文档的关系
                self.create_relation(
                    doc_entity_id, entity_id, "contains", {"chunk_id": doc_info["chunk_id"]}
                )

            # 创建关系
            for relation in result.get("relations", []):
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
                    source_id = self.create_entity(source_name, "concept", source_metadata)
                    entity_ids[source_name] = source_id
                else:
                    source_id = entity_ids[source_name]

                if target_name not in entity_ids:
                    target_metadata = {
                        "description": f"从关系提取的实体：{relation_type}关系的目标",
                        "source_document": doc_title,
                        "auto_generated": True,
                    }
                    target_id = self.create_entity(target_name, "concept", target_metadata)
                    entity_ids[target_name] = target_id
                else:
                    target_id = entity_ids[target_name]

                # 创建关系
                relation_metadata = {
                    "description": relation.get("description", ""),
                    "source_document": doc_title,
                    "chunk_id": doc_info["chunk_id"],
                }

                self.create_relation(source_id, target_id, relation_type, relation_metadata)

            # 存储观察
            for idx, obs in enumerate(result.get("observations", [])):
                if not obs.strip():
                    continue

                self.create_observation(
                    doc_entity_id,
                    obs,
                    {
                        "type": "extracted_observation",
                        "order": idx,
                        "chunk_id": doc_info["chunk_id"],
                    },
                )

            # 处理标签
            for tag in result.get("tags", []):
                tag_name = tag.strip()
                if not tag_name:
                    continue

                # 检查标签是否已存在
                tag_id = self.get_entity_id(tag_name)
                if not tag_id:
                    tag_id = self.create_entity(tag_name, "tag", {"source_document": doc_title})

                # 创建文档与标签的关系
                self.create_relation(doc_entity_id, tag_id, "tagged_with")

        # 统计处理结果
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM entities")
        entity_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM observations")
        observation_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM relations")
        relation_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM vector_chunks")
        vector_chunk_count = c.fetchone()[0]

        c.execute("SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC")
        type_stats = c.fetchall()

        conn.close()

        print(f"\n导入完成! 共处理了 {len(documents)} 个文件。")
        print(f"数据已存储到: {self.db_path}")
        print(f"向量索引已保存到: {self.vector_index_path}")

        print("\n数据库统计信息:")
        print(f"- 实体总数: {entity_count}")
        print(f"- 观察总数: {observation_count}")
        print(f"- 关系总数: {relation_count}")
        print(f"- 向量块总数: {vector_chunk_count}")

        print("\n实体类型分布:")
        for type_name, count in type_stats:
            print(f"- {type_name}: {count}")

    def create_query_interface(self):
        """创建查询接口

        Returns:
            ConversationalRetrievalChain: 查询链
        """
        # 加载向量存储
        vector_store = FAISS.load_local(self.vector_index_path, self.embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # 创建对话存储
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # 创建对话检索链
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, retriever=retriever, memory=memory, verbose=True
        )

        return qa_chain


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
