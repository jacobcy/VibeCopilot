#!/usr/bin/env python3
"""
知识库查询命令行工具
提供自然语言查询接口和命令行参数支持
"""

import argparse
import os
import sys
from pathlib import Path

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from adapters.basic_memory.utils.api_utils import get_openai_api_key


class KnowledgeQuerier:
    """知识查询器

    使用向量检索和LLM实现文档知识的自然语言查询
    """

    def __init__(self, index_path=None, model="gpt-4o-mini", db_path=None):
        """初始化知识查询器

        Args:
            index_path: 向量索引路径
            model: 使用的LLM模型
            db_path: 数据库路径
        """
        # 设置默认路径
        self.base_path = Path(os.path.expanduser("/Users/chenyi/basic-memory"))

        if index_path:
            self.vector_index_path = Path(index_path)
        else:
            self.vector_index_path = self.base_path / "vector_index"

        # 确保API密钥已设置
        api_key = get_openai_api_key()
        if not api_key:
            print("错误: 未设置OPENAI_API_KEY环境变量，无法使用LLM查询功能")
            sys.exit(1)

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
        # 检查向量索引目录是否存在
        if not self.vector_index_path.exists():
            print(f"错误: 向量索引目录不存在: {self.vector_index_path}")
            print("请先使用LangChain解析器处理文档生成向量索引")
            sys.exit(1)

        try:
            # 加载向量存储
            vector_store = FAISS.load_local(str(self.vector_index_path), self.embeddings, allow_dangerous_deserialization=True)
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})

            # 创建对话存储
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

            # 创建对话检索链
            qa_chain = ConversationalRetrievalChain.from_llm(llm=self.llm, retriever=retriever, memory=memory, verbose=False)

            return qa_chain
        except Exception as e:
            print(f"错误: 加载向量存储失败: {e}")
            print("请确保已正确处理文档并生成向量索引")
            sys.exit(1)

    def query(self, question):
        """查询知识库

        Args:
            question: 查询问题

        Returns:
            str: 查询结果
        """
        result = self.qa_chain.invoke({"question": question})
        return result["answer"]

    def interactive_mode(self):
        """交互模式"""
        print("Basic Memory 知识库查询工具")
        print("--------------------------------------------")
        print(f"向量索引: {self.vector_index_path}")
        print(f"模型: {self.llm.model_name}")
        print("输入 'exit'、'quit' 或 'q' 退出")
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
                print(f"{answer}")

            except KeyboardInterrupt:
                print("\n已退出")
                break
            except Exception as e:
                print(f"查询出错: {e}")


def setup_query_parser(subparsers):
    """设置查询命令的解析器

    Args:
        subparsers: 父解析器的子解析器
    """
    query_parser = subparsers.add_parser("query", help="查询知识库")
    query_parser.add_argument("--index", default=None, help="向量索引路径")
    query_parser.add_argument("--model", default="gpt-4o-mini", help="使用的LLM模型")
    query_parser.add_argument(
        "--db",
        default="/Users/chenyi/basic-memory/main.db",
        help="数据库路径 (默认: /Users/chenyi/basic-memory/main.db)",
    )
    query_parser.add_argument("--interactive", "-i", action="store_true", help="启用交互模式")
    query_parser.add_argument("question", nargs="?", help="查询问题")

    return query_parser


def handle_query(args):
    """处理查询命令

    Args:
        args: 解析后的命令行参数
    """
    # 初始化查询器
    querier = KnowledgeQuerier(index_path=args.index, model=args.model, db_path=args.db)

    # 判断是否使用交互模式
    if args.interactive:
        querier.interactive_mode()
    elif args.question:
        answer = querier.query(args.question)
        print(answer)
    else:
        print("错误: 请提供查询问题或使用交互模式 (-i)")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Basic Memory知识库查询工具")
    parser.add_argument("--index", default=None, help="向量索引路径")
    parser.add_argument("--model", default="gpt-4o-mini", help="使用的LLM模型")
    parser.add_argument("--interactive", "-i", action="store_true", help="启用交互模式")
    parser.add_argument("question", nargs="?", help="查询问题")

    args = parser.parse_args()

    # 判断是否使用交互模式
    if args.interactive:
        querier = KnowledgeQuerier(index_path=args.index, model=args.model)
        querier.interactive_mode()
    elif args.question:
        querier = KnowledgeQuerier(index_path=args.index, model=args.model)
        answer = querier.query(args.question)
        print(answer)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
