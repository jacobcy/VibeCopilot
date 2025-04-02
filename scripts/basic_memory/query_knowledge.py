#!/usr/bin/env python3
"""
基于LangChain和Basic Memory的知识库查询工具
提供自然语言交互接口和命令行参数支持
"""

import argparse
import os
import sys
from pathlib import Path

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


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


class KnowledgeQuerier:
    """知识查询器

    使用向量检索和LLM实现文档知识的自然语言查询
    """

    def __init__(self, index_path=None, model="gpt-4o-mini"):
        """初始化知识查询器

        Args:
            index_path (str, optional): 向量索引路径. Defaults to None.
            model (str, optional): 使用的LLM模型. Defaults to "gpt-4o-mini".
        """
        # 设置默认路径
        self.base_path = Path(os.path.expanduser("/Users/chenyi/basic-memory"))

        if index_path:
            self.vector_index_path = Path(index_path)
        else:
            self.vector_index_path = self.base_path / "vector_index"

        # 初始化LLM和embedding模型
        self.llm = ChatOpenAI(model=model, temperature=0)

        self.embeddings = OpenAIEmbeddings()

        # 创建查询链
        self.qa_chain = self.create_query_chain()

    def create_query_chain(self):
        """创建查询链

        Returns:
            ConversationalRetrievalChain: 查询链
        """
        # 加载向量存储
        vector_store = FAISS.load_local(
            str(self.vector_index_path), self.embeddings, allow_dangerous_deserialization=True
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # 创建对话存储
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # 创建对话检索链
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm, retriever=retriever, memory=memory, verbose=False
        )

        return qa_chain

    def query(self, question):
        """查询知识库

        Args:
            question (str): 查询问题

        Returns:
            str: 查询结果
        """
        result = self.qa_chain.invoke({"question": question})
        return result["answer"]

    def interactive_mode(self):
        """交互模式"""
        print("知识库查询工具 (输入 'exit' 或 'quit' 退出)")
        print("--------------------------------------------")

        while True:
            try:
                question = input("\n问题> ")
                question = question.strip()

                if question.lower() in ["exit", "quit", "q"]:
                    break

                if not question:
                    continue

                print("\n回答:")
                answer = self.query(question)
                print(f"\n{answer}")

            except KeyboardInterrupt:
                print("\n已退出")
                break
            except Exception as e:
                print(f"查询出错: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="基于向量检索的知识库查询工具")
    parser.add_argument("--index", default=None, help="向量索引路径")
    parser.add_argument("--model", default="gpt-4o-mini", help="使用的LLM模型")
    parser.add_argument("--query", help="查询问题")

    args = parser.parse_args()

    if not args.query:
        parser.error("请提供要查询的问题 (--query)")

    # 初始化查询器并执行查询
    querier = KnowledgeQuerier(index_path=args.index, model=args.model)
    answer = querier.query(args.query)

    print(answer)


if __name__ == "__main__":
    main()
