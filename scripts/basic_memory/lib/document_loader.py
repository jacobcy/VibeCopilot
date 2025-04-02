#!/usr/bin/env python3
"""
文档加载和预处理模块
"""

from pathlib import Path
from typing import Any, Dict, List

import frontmatter
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentLoader:
    """文档加载和预处理类"""

    def __init__(self, source_dir: str):
        """初始化文档加载器

        Args:
            source_dir: 源文档目录
        """
        self.source_dir = Path(source_dir)

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n#### ", "\n", " ", ""],
            keep_separator=True,
        )

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

    def split_document(self, document_content: str) -> List[str]:
        """分割文档内容

        Args:
            document_content: 文档内容

        Returns:
            List[str]: 分割后的文本块
        """
        return self.text_splitter.split_text(document_content)

    def get_document_count(self) -> int:
        """获取文档数量

        Returns:
            int: 文档数量
        """
        return len(list(self.source_dir.rglob("*.md")))

    def get_document_sizes(self) -> Dict[str, int]:
        """获取文档大小统计

        Returns:
            Dict[str, int]: 文档路径和大小（字节）
        """
        return {
            str(md_file.relative_to(self.source_dir)): md_file.stat().st_size
            for md_file in self.source_dir.rglob("*.md")
        }
