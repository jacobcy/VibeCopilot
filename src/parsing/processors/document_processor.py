"""
文档处理器

专门用于处理文档文件的处理器。
"""

import asyncio
import os
from glob import glob
from typing import Any, Dict, List, Optional

from src.parsing.parser_factory import create_parser
from src.parsing.parsers.llm_parser import LLMParser


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

        # 创建LLM解析器
        self.parser = LLMParser(self.config)

    def process_document_text(self, content: str) -> Dict[str, Any]:
        """
        处理文档文本

        Args:
            content: 文档文本内容

        Returns:
            处理结果
        """
        # 直接使用LLM解析器处理文档内容
        try:
            result = self.parser.parse(content, content_type="document")

            # 确保success字段存在
            if "success" not in result:
                result["success"] = True

            return result
        except Exception as e:
            # 处理解析错误
            return {
                "success": False,
                "error": f"解析文档内容失败: {str(e)}",
                "content_type": "document",
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }

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

    def process_document_directory(self, directory_path: str, pattern="**/*.md") -> List[Dict[str, Any]]:
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
        }

        # 添加文件信息（如果有）
        if "file_info" in doc_result:
            metadata["file_path"] = doc_result["file_info"]["path"]
            metadata["file_name"] = doc_result["file_info"]["name"]
            metadata["directory"] = doc_result["file_info"]["directory"]

        return metadata

    def generate_document_summary(self, content: str, max_length: int = 150) -> str:
        """
        生成文档摘要

        使用LLM解析器生成文档摘要，提取文档的主要内容要点

        Args:
            content: 文档文本内容
            max_length: 摘要最大长度

        Returns:
            str: 生成的文档摘要
        """
        try:
            # 构建摘要提示
            summary_prompt = {"task": "summarize", "content": content, "max_length": max_length, "content_type": "document"}

            # 使用LLM解析器生成摘要
            result = self.parser.parse(content, content_type="summary", custom_instructions=f"生成不超过{max_length}字符的文档摘要，保留核心内容和主要观点")

            # 检查结果，提取摘要
            if isinstance(result, dict) and "summary" in result:
                summary = result["summary"]
            elif isinstance(result, dict) and "content" in result:
                summary = result["content"]
            else:
                # 如果没有得到有效摘要，使用简单方法提取
                sentences = content.split("。")[:3]  # 取前三句
                summary = "。".join(sentences)
                if len(summary) > max_length:
                    summary = summary[: max_length - 3] + "..."

            # 确保摘要不超过最大长度
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            return summary
        except Exception as e:
            # 发生错误时返回简单摘要
            return content[: max_length - 3] + "..." if len(content) > max_length else content
