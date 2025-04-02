#!/usr/bin/env python3
"""
向量存储和检索模块
"""

import os
from pathlib import Path
from typing import Dict, List

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from scripts.basic_memory.lib.utils import get_openai_api_key


class VectorManager:
    """向量存储管理器"""

    def __init__(self, vector_index_path: str, model: str = "gpt-4o-mini"):
        """初始化向量存储管理器

        Args:
            vector_index_path: 向量索引存储路径
            model: 查询使用的模型
        """
        self.vector_index_path = vector_index_path
        self.model = model
        self.api_key = get_openai_api_key()

        if not self.api_key:
            raise ValueError("无法获取OpenAI API密钥，请检查环境变量或.env文件")

        # 确保目录存在
        Path(self.vector_index_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings()

        # 初始化LLM
        self.llm = ChatOpenAI(model=self.model, temperature=0.2, streaming=False, verbose=False)

    def create_vector_store(self, text_chunks: List[str]) -> FAISS:
        """创建向量存储

        Args:
            text_chunks: 文本块列表

        Returns:
            FAISS: 向量存储对象
        """
        if not text_chunks:
            raise ValueError("文本块列表为空")

        print(f"创建向量索引，共 {len(text_chunks)} 个文本块")
        vector_store = FAISS.from_texts(text_chunks, self.embeddings)
        return vector_store

    def save_vector_store(self, vector_store: FAISS) -> None:
        """保存向量存储

        Args:
            vector_store: 向量存储对象
        """
        os.makedirs(os.path.dirname(self.vector_index_path), exist_ok=True)
        vector_store.save_local(self.vector_index_path)
        print(f"向量索引已保存到: {self.vector_index_path}")

    def load_vector_store(self) -> FAISS:
        """加载向量存储

        Returns:
            FAISS: 向量存储对象
        """
        if not os.path.exists(self.vector_index_path):
            raise FileNotFoundError(f"向量索引不存在: {self.vector_index_path}")

        return FAISS.load_local(self.vector_index_path, self.embeddings)

    def create_query_interface(self):
        """创建查询接口

        Returns:
            ConversationalRetrievalChain: 查询链
        """
        # 加载向量存储
        vector_store = self.load_vector_store()
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # 创建对话存储
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # 创建对话检索链
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, retriever=retriever, memory=memory, verbose=True
        )

        return qa_chain
