"""
同步编排器

负责编排同步流程，将不同类型的内容同步到相应的目标。
"""

import logging
import os
from glob import glob
from typing import Any, Dict, List, Optional, Set

from src.memory.services import MemoryServiceImpl
from src.parsing.processors.document_processor import DocumentProcessor
from src.parsing.processors.rule_processor import RuleProcessor

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """
    同步编排器

    负责协调不同类型内容的同步流程:
    1. 确定需要同步的文件
    2. 识别文件类型
    3. 调用相应的处理器处理文件
    4. 调用内存服务执行存储
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化同步编排器

        Args:
            config: 配置参数
        """
        self.config = config or {}

        # 创建处理器
        self.rule_processor = RuleProcessor(config=self.config.get("rule_processor"))
        self.document_processor = DocumentProcessor(config=self.config.get("document_processor"))

        # 获取内存服务实例
        self.memory_service = MemoryServiceImpl(self.config)

        # 默认目录配置
        self.rule_dir = self.config.get("rule_dir", ".cursor/rules")
        self.doc_dir = self.config.get("doc_dir", "docs")

    async def orchestrate_sync(self, changed_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        编排同步流程

        Args:
            changed_files: 已更改的文件路径列表，如果为None则同步所有内容

        Returns:
            同步结果
        """
        if changed_files is None:
            # 同步所有规则和文档
            return await self._sync_all()
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
            rule_result = await self._sync_rules(rule_files)
            doc_result = await self._sync_documents(doc_files)

            return {
                "success": True,
                "rules": rule_result,
                "documents": doc_result,
                "total_synced": rule_result.get("synced_count", 0) + doc_result.get("synced_count", 0),
            }

    async def _sync_all(self) -> Dict[str, Any]:
        """
        同步所有内容

        Returns:
            同步结果
        """
        rule_result = await self._sync_rules()
        doc_result = await self._sync_documents()

        return {
            "success": True,
            "rules": rule_result,
            "documents": doc_result,
            "total_synced": rule_result.get("synced_count", 0) + doc_result.get("synced_count", 0),
        }

    async def _sync_rules(self, rule_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步规则文件

        Args:
            rule_files: 规则文件路径列表，如果为None则同步所有规则

        Returns:
            同步结果
        """
        # 处理规则文件
        if rule_files is None:
            # 默认规则目录
            rule_results = await self.rule_processor.process_rule_directory(self.rule_dir)
        else:
            # 处理指定的规则文件
            rule_results = []
            for file_path in rule_files:
                if os.path.exists(file_path):
                    result = await self.rule_processor.process_rule_file(file_path)
                    rule_results.append(result)

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

        # 调用内存服务存储
        if texts:
            permalinks = await self.memory_service.execute_storage(texts, metadata_list, "rules")

        return {
            "success": True,
            "synced_count": len(permalinks),
            "total_count": len(rule_results),
            "permalinks": permalinks,
        }

    async def _sync_documents(self, doc_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        同步文档文件

        Args:
            doc_files: 文档文件路径列表，如果为None则同步所有文档

        Returns:
            同步结果
        """
        # 处理文档文件
        if doc_files is None:
            # 默认文档目录
            doc_results = self.document_processor.process_document_directory(self.doc_dir)
        else:
            # 处理指定的文档文件
            doc_results = []
            for file_path in doc_files:
                if os.path.exists(file_path):
                    result = self.document_processor.process_document_file(file_path)
                    doc_results.append(result)

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

        # 调用内存服务存储
        if texts:
            permalinks = await self.memory_service.execute_storage(texts, metadata_list, "documents")

        return {
            "success": True,
            "synced_count": len(permalinks),
            "total_count": len(doc_results),
            "permalinks": permalinks,
        }

    async def sync_by_type(self, content_type: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        根据内容类型同步文件

        Args:
            content_type: 内容类型 ("rule" 或 "document")
            files: 文件路径列表，如果为None则同步指定类型的所有内容

        Returns:
            同步结果
        """
        if content_type == "rule":
            result = await self._sync_rules(files)
            return {
                "success": True,
                "rules": result,
                "total_synced": result.get("synced_count", 0),
            }
        elif content_type == "document":
            result = await self._sync_documents(files)
            return {
                "success": True,
                "documents": result,
                "total_synced": result.get("synced_count", 0),
            }
        else:
            raise ValueError(f"不支持的内容类型: {content_type}")
