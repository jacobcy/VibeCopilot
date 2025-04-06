#!/usr/bin/env python3
"""
文档加载器模块
负责加载和分割各种格式的文档
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)


class DocumentLoader:
    """文档加载器

    负责从指定目录加载各种格式的文档，并进行预处理和分割
    """

    def __init__(
        self, source_dir: Union[str, Path], chunk_size: int = 1000, chunk_overlap: int = 200
    ):
        """初始化文档加载器

        Args:
            source_dir: 源文档目录
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
        """
        self.source_dir = Path(source_dir) if isinstance(source_dir, str) else source_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 创建文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def load_documents(self) -> List[Dict]:
        """加载目录中的所有文档

        Returns:
            List[Dict]: 文档列表，每个文档包含标题和内容
        """
        documents = []

        # 检查目录是否存在
        if not self.source_dir.exists() or not self.source_dir.is_dir():
            print(f"错误: 目录不存在: {self.source_dir}")
            return documents

        print(f"加载文档从目录: {self.source_dir}")

        # 加载Markdown文件
        md_docs = self._load_markdown_files()
        if md_docs:
            documents.extend(md_docs)
            print(f"已加载 {len(md_docs)} 个Markdown文件")

        # 加载PDF文件
        pdf_docs = self._load_pdf_files()
        if pdf_docs:
            documents.extend(pdf_docs)
            print(f"已加载 {len(pdf_docs)} 个PDF文件")

        # 加载文本文件
        txt_docs = self._load_text_files()
        if txt_docs:
            documents.extend(txt_docs)
            print(f"已加载 {len(txt_docs)} 个文本文件")

        return documents

    def _load_markdown_files(self) -> List[Dict]:
        """加载Markdown文件

        Returns:
            List[Dict]: 文档列表
        """
        try:
            md_loader = DirectoryLoader(
                self.source_dir,
                glob="**/*.md",
                loader_cls=UnstructuredMarkdownLoader,
                show_progress=True,
            )
            md_docs = md_loader.load()

            # 转换为统一格式
            result = []
            for doc in md_docs:
                title = os.path.relpath(doc.metadata.get("source"), str(self.source_dir))
                result.append(
                    {
                        "title": title,
                        "content": doc.page_content,
                        "metadata": {"source": doc.metadata.get("source"), "type": "markdown"},
                    }
                )

            return result
        except Exception as e:
            print(f"加载Markdown文件时出错: {e}")
            return []

    def _load_pdf_files(self) -> List[Dict]:
        """加载PDF文件

        Returns:
            List[Dict]: 文档列表
        """
        try:
            pdf_loader = DirectoryLoader(
                self.source_dir,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True,
            )
            pdf_docs = pdf_loader.load()

            # 转换为统一格式并按文件合并页面
            result = []
            doc_dict = {}

            for doc in pdf_docs:
                source = doc.metadata.get("source")
                title = os.path.relpath(source, str(self.source_dir))
                page = doc.metadata.get("page", 0)

                if source not in doc_dict:
                    doc_dict[source] = {
                        "title": title,
                        "content": f"[Page {page+1}]\n{doc.page_content}\n\n",
                        "metadata": {"source": source, "type": "pdf", "pages": [page]},
                    }
                else:
                    doc_dict[source]["content"] += f"[Page {page+1}]\n{doc.page_content}\n\n"
                    doc_dict[source]["metadata"]["pages"].append(page)

            for doc_data in doc_dict.values():
                result.append(doc_data)

            return result
        except Exception as e:
            print(f"加载PDF文件时出错: {e}")
            return []

    def _load_text_files(self) -> List[Dict]:
        """加载文本文件

        Returns:
            List[Dict]: 文档列表
        """
        try:
            txt_loader = DirectoryLoader(
                self.source_dir,
                glob="**/*.txt",
                loader_cls=TextLoader,
                show_progress=True,
            )
            txt_docs = txt_loader.load()

            # 转换为统一格式
            result = []
            for doc in txt_docs:
                title = os.path.relpath(doc.metadata.get("source"), str(self.source_dir))
                result.append(
                    {
                        "title": title,
                        "content": doc.page_content,
                        "metadata": {"source": doc.metadata.get("source"), "type": "text"},
                    }
                )

            return result
        except Exception as e:
            print(f"加载文本文件时出错: {e}")
            return []

    def split_document(self, content: str) -> List[str]:
        """分割文档内容为较小的块

        Args:
            content: 文档内容

        Returns:
            List[str]: 分割后的文档块列表
        """
        chunks = self.text_splitter.split_text(content)
        return chunks
