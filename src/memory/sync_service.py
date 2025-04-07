"""
同步服务

负责同步本地内容到Basic Memory。
"""

import os
from typing import Any, Dict, List, Optional, Set

from src.db.vector.memory_adapter import BasicMemoryAdapter
from src.parsing.processors.document_processor import DocumentProcessor
from src.parsing.processors.rule_processor import RuleProcessor


class SyncService:
    """
    同步服务

    提供将本地规则和文档同步到Basic Memory的功能。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化同步服务

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建处理器
        self.rule_processor = RuleProcessor()
        self.document_processor = DocumentProcessor()

        # 创建向量存储适配器
        self.vector_store = BasicMemoryAdapter(self.config.get("vector_store"))

    async def sync_rules(self, rule_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步规则文件

        Args:
            rule_files: 规则文件路径列表，如果为None则同步所有规则

        Returns:
            同步结果
        """
        if rule_files is None:
            # 默认规则目录
            rule_dir = self.config.get("rule_dir", ".cursor/rules")
            rule_results = self.rule_processor.process_rule_directory(rule_dir)
        else:
            # 处理指定的规则文件
            rule_results = []
            for file_path in rule_files:
                if os.path.exists(file_path):
                    rule_results.append(self.rule_processor.process_rule_file(file_path))

        # 提取规则内容和元数据
        texts = []
        metadata_list = []
        permalinks = []

        for result in rule_results:
            if result.get("success", False):
                # 提取内容
                content = result.get("content", "")

                # 提取元数据
                metadata = {
                    "title": result.get("title", ""),
                    "type": "rule",
                    "tags": "rule",
                    "rule_type": result.get("front_matter", {}).get("type", ""),
                    "description": result.get("front_matter", {}).get("description", ""),
                }

                # 如果有文件信息，添加到元数据
                if "file_info" in result:
                    metadata["file_path"] = result["file_info"]["path"]
                    metadata["file_name"] = result["file_info"]["name"]
                    metadata["directory"] = result["file_info"]["directory"]

                texts.append(content)
                metadata_list.append(metadata)

        # 同步到向量存储
        if texts:
            permalinks = await self.vector_store.store(texts, metadata_list, "rules")

        return {
            "success": True,
            "synced_count": len(permalinks),
            "total_count": len(rule_results),
            "permalinks": permalinks,
        }

    async def sync_documents(self, doc_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步文档文件

        Args:
            doc_files: 文档文件路径列表，如果为None则同步所有文档

        Returns:
            同步结果
        """
        if doc_files is None:
            # 默认文档目录
            doc_dir = self.config.get("doc_dir", "docs")
            doc_results = self.document_processor.process_document_directory(doc_dir)
        else:
            # 处理指定的文档文件
            doc_results = []
            for file_path in doc_files:
                if os.path.exists(file_path):
                    doc_results.append(self.document_processor.process_document_file(file_path))

        # 提取文档内容和元数据
        texts = []
        metadata_list = []
        permalinks = []

        for result in doc_results:
            if result.get("success", False):
                # 提取内容
                content = result.get("content", "")

                # 提取元数据
                metadata = {
                    "title": result.get("title", ""),
                    "type": "document",
                    "tags": "document",
                    "word_count": result.get("metadata", {}).get("word_count", 0),
                    "line_count": result.get("metadata", {}).get("line_count", 0),
                }

                # 如果有文件信息，添加到元数据
                if "file_info" in result:
                    metadata["file_path"] = result["file_info"]["path"]
                    metadata["file_name"] = result["file_info"]["name"]
                    metadata["directory"] = result["file_info"]["directory"]

                texts.append(content)
                metadata_list.append(metadata)

        # 同步到向量存储
        if texts:
            permalinks = await self.vector_store.store(texts, metadata_list, "documents")

        return {
            "success": True,
            "synced_count": len(permalinks),
            "total_count": len(doc_results),
            "permalinks": permalinks,
        }

    async def sync_all(self, changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步所有内容

        Args:
            changed_files: 已更改的文件路径列表，如果为None则同步所有内容

        Returns:
            同步结果
        """
        if changed_files is None:
            # 同步所有规则和文档
            rule_result = await self.sync_rules()
            doc_result = await self.sync_documents()
        else:
            # 根据文件类型分类
            rule_files = []
            doc_files = []

            for file_path in changed_files:
                if file_path.endswith(".mdc"):
                    rule_files.append(file_path)
                elif file_path.endswith(".md"):
                    doc_files.append(file_path)

            # 同步已更改的文件
            rule_result = await self.sync_rules(rule_files)
            doc_result = await self.sync_documents(doc_files)

        return {
            "success": True,
            "rules": rule_result,
            "documents": doc_result,
            "total_synced": rule_result.get("synced_count", 0) + doc_result.get("synced_count", 0),
        }
