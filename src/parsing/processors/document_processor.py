"""
文档处理器

专门用于处理文档文件的处理器。
"""

import os
from glob import glob
from typing import Any, Dict, List, Optional

from src.parsing.parser_factory import create_parser


class DocumentProcessor:
    """
    文档处理器

    提供解析和处理文档文件的专门功能。
    """

    def __init__(self, backend="openai", config=None):
        """
        初始化文档处理器

        Args:
            backend: 解析后端，如'openai'、'ollama'、'regex'
            config: 配置参数
        """
        self.backend = backend
        self.config = config or {}

        # 创建解析器
        self.parser = create_parser("document", backend, config)

    def process_document_text(self, content: str) -> Dict[str, Any]:
        """
        处理文档文本

        Args:
            content: 文档文本内容

        Returns:
            处理结果
        """
        # 解析文档内容
        result = self.parser.parse_text(content, "document")

        # 提取关键信息
        summary = self._generate_summary(result)
        toc = self._generate_toc(result)

        # 添加处理结果
        result["processed"] = {"summary": summary, "toc": toc}

        return result

    def process_document_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理文档文件

        Args:
            file_path: 文档文件路径

        Returns:
            处理结果
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 处理文档文本
        result = self.process_document_text(content)

        # 添加文件信息
        result["file_info"] = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "directory": os.path.dirname(file_path),
        }

        return result

    def process_document_directory(
        self, directory_path: str, pattern="**/*.md"
    ) -> List[Dict[str, Any]]:
        """
        处理文档目录

        Args:
            directory_path: 文档目录路径
            pattern: 文件匹配模式

        Returns:
            处理结果列表
        """
        # 检查目录是否存在
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return [{"success": False, "error": f"Directory not found: {directory_path}"}]

        # 查找文档文件
        doc_files = glob(os.path.join(directory_path, pattern), recursive=True)

        # 处理每个文档文件
        results = []
        for file_path in doc_files:
            result = self.process_document_file(file_path)
            results.append(result)

        return results

    def extract_document_metadata(self, doc_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取文档元数据

        Args:
            doc_result: 文档处理结果

        Returns:
            文档元数据
        """
        metadata = {
            "title": doc_result.get("title", ""),
            "word_count": doc_result.get("metadata", {}).get("word_count", 0),
            "line_count": doc_result.get("metadata", {}).get("line_count", 0),
            "has_toc": bool(doc_result.get("processed", {}).get("toc")),
            "summary": doc_result.get("processed", {}).get("summary", ""),
        }

        # 添加文件信息（如果有）
        if "file_info" in doc_result:
            metadata["file_path"] = doc_result["file_info"]["path"]
            metadata["file_name"] = doc_result["file_info"]["name"]
            metadata["directory"] = doc_result["file_info"]["directory"]

        return metadata

    def _generate_summary(self, doc_result: Dict[str, Any]) -> str:
        """
        生成文档摘要

        Args:
            doc_result: 文档处理结果

        Returns:
            文档摘要
        """
        # 这里简化实现，实际可能需要更复杂的逻辑
        title = doc_result.get("title", "")
        headings = doc_result.get("structure", {}).get("headings", [])

        summary = f"Document: {title}\n"

        if headings:
            summary += "Main sections:\n"
            for heading in headings[:5]:  # 只取前5个标题
                if heading.get("level") == 2:  # 只取二级标题
                    summary += f"- {heading.get('text')}\n"

        return summary.strip()

    def _generate_toc(self, doc_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成文档目录

        Args:
            doc_result: 文档处理结果

        Returns:
            文档目录
        """
        headings = doc_result.get("structure", {}).get("headings", [])

        # 构建目录树
        toc = []
        current_parents = [None] * 10  # 假设最多10级标题

        for heading in headings:
            level = heading.get("level")
            text = heading.get("text")

            item = {"level": level, "text": text, "children": []}

            if level == 1:
                toc.append(item)
                current_parents[0] = item
            else:
                parent_index = level - 2
                if parent_index >= 0 and current_parents[parent_index] is not None:
                    current_parents[parent_index]["children"].append(item)
                    current_parents[level - 1] = item

        return toc
