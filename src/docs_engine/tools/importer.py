"""
导入工具模块

提供从文件系统导入文档的功能
"""

import glob
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.docs_engine.api import BlockManager, DocumentEngine, LinkManager
from src.docs_engine.utils.markdown_parser import extract_metadata, parse_markdown_to_blocks
from src.models.db.docs_engine import DocumentStatus


class MarkdownImporter:
    """Markdown导入工具

    从文件系统导入Markdown文档到数据库
    """

    def __init__(
        self,
        document_engine: DocumentEngine,
        block_manager: BlockManager,
        link_manager: LinkManager,
    ):
        """初始化

        Args:
            document_engine: 文档引擎实例
            block_manager: 块管理器实例
            link_manager: 链接管理器实例
        """
        self.document_engine = document_engine
        self.block_manager = block_manager
        self.link_manager = link_manager

        # 导入过程的统计信息
        self.stats = {"total": 0, "imported": 0, "skipped": 0, "failed": 0, "links_created": 0}

        # 文档路径到ID的映射
        self.path_to_id_map = {}

    def import_directory(self, directory_path: str, pattern: str = "**/*.md") -> Dict[str, Any]:
        """导入目录中的Markdown文件

        Args:
            directory_path: 目录路径
            pattern: 文件匹配模式

        Returns:
            导入统计信息
        """
        # 重置统计信息
        self.stats = {"total": 0, "imported": 0, "skipped": 0, "failed": 0, "links_created": 0}

        # 查找所有匹配的文件
        base_path = Path(directory_path)
        markdown_files = list(base_path.glob(pattern))
        self.stats["total"] = len(markdown_files)

        # 第一遍：导入所有文档，并建立路径到ID的映射
        for file_path in markdown_files:
            self._import_file(file_path, base_path, create_links=False)

        # 第二遍：处理文档之间的链接
        for file_path in markdown_files:
            self._process_file_links(file_path, base_path)

        return self.stats

    def import_file(self, file_path: str, base_path: Optional[str] = None) -> Optional[str]:
        """导入单个Markdown文件

        Args:
            file_path: 文件路径
            base_path: 基础路径（可选），用于计算相对路径

        Returns:
            导入的文档ID或None（导入失败）
        """
        self.stats = {"total": 1, "imported": 0, "skipped": 0, "failed": 0, "links_created": 0}

        path = Path(file_path)
        base = Path(base_path) if base_path else path.parent

        # 导入文件
        doc_id = self._import_file(path, base, create_links=True)

        return doc_id

    def _import_file(
        self, file_path: Path, base_path: Path, create_links: bool = False
    ) -> Optional[str]:
        """导入文件的内部实现

        Args:
            file_path: 文件路径
            base_path: 基础路径，用于计算相对路径
            create_links: 是否创建链接

        Returns:
            导入的文档ID或None（导入失败）
        """
        try:
            # 计算相对路径，用作元数据
            rel_path = str(file_path.relative_to(base_path))

            # 读取文件内容
            content = file_path.read_text(encoding="utf-8")

            # 提取元数据
            metadata, content_without_metadata = extract_metadata(content)

            # 设置元数据
            if not metadata:
                metadata = {}

            metadata["source_path"] = rel_path

            # 使用文件名作为标题（如果元数据中没有标题）
            title = metadata.get("title", file_path.stem)

            # 创建文档
            document = self.document_engine.create_document(title=title, metadata=metadata)

            # 记录路径到ID的映射
            self.path_to_id_map[rel_path] = document.id

            # 解析内容为块
            blocks = parse_markdown_to_blocks(content_without_metadata)

            # 创建块
            for block_data in blocks:
                self.block_manager.create_block(
                    document_id=document.id,
                    content=block_data["content"],
                    block_type=block_data["type"],
                    metadata=block_data["metadata"],
                )

            # 处理链接
            if create_links:
                created_links = self.link_manager.process_document_links(document.id, content)
                self.stats["links_created"] += len(created_links)

            # 更新统计信息
            self.stats["imported"] += 1

            # 如果元数据中指定了状态，更新文档状态
            if "status" in metadata:
                status = metadata["status"]
                if status == "active":
                    self.document_engine.publish_document(document.id)

            return document.id

        except Exception as e:
            print(f"导入失败 {file_path}: {str(e)}")
            self.stats["failed"] += 1
            return None

    def _process_file_links(self, file_path: Path, base_path: Path) -> None:
        """处理文件中的链接

        使用第一遍建立的路径到ID的映射，解析文档中的相对路径链接

        Args:
            file_path: 文件路径
            base_path: 基础路径，用于计算相对路径
        """
        try:
            # 计算相对路径
            rel_path = str(file_path.relative_to(base_path))

            # 获取文档ID
            doc_id = self.path_to_id_map.get(rel_path)
            if not doc_id:
                return

            # 读取文件内容
            content = file_path.read_text(encoding="utf-8")

            # 提取链接
            links = self._extract_markdown_links(content, file_path, base_path)

            # 创建链接
            for link in links:
                if link["target_doc_id"] in self.path_to_id_map:
                    self.link_manager.create_link(
                        source_doc_id=doc_id,
                        target_doc_id=self.path_to_id_map[link["target_doc_id"]],
                        text=link["text"],
                    )
                    self.stats["links_created"] += 1

        except Exception as e:
            print(f"处理链接失败 {file_path}: {str(e)}")

    def _extract_markdown_links(
        self, content: str, file_path: Path, base_path: Path
    ) -> List[Dict[str, Any]]:
        """提取Markdown内容中的链接

        Args:
            content: Markdown内容
            file_path: 当前文件路径
            base_path: 基础路径

        Returns:
            链接信息列表
        """
        links = []

        # 匹配Markdown链接: [text](target)
        pattern = r"\[(.*?)\]\((.*?)\)"

        for match in re.finditer(pattern, content):
            link_text = match.group(1)
            link_target = match.group(2)

            # 忽略外部链接
            if link_target.startswith(("http://", "https://", "ftp://", "mailto:")):
                continue

            # 处理相对路径
            target_path = self._resolve_relative_path(link_target, file_path, base_path)
            if target_path:
                links.append({"text": link_text, "target_doc_id": target_path})

        return links

    def _resolve_relative_path(
        self, link_path: str, current_file: Path, base_path: Path
    ) -> Optional[str]:
        """解析相对路径链接

        Args:
            link_path: 链接路径
            current_file: 当前文件路径
            base_path: 基础路径

        Returns:
            解析后的相对路径或None
        """
        try:
            # 移除URL片段
            link_path = link_path.split("#")[0]

            # 如果是空链接，返回None
            if not link_path:
                return None

            # 处理相对路径
            if not link_path.startswith("/"):
                # 相对于当前文件的路径
                target = (current_file.parent / link_path).resolve()
            else:
                # 相对于根目录的路径
                target = (base_path / link_path.lstrip("/")).resolve()

            # 确保目标在基础路径内
            if base_path in target.parents or base_path == target:
                # 计算相对路径
                return str(target.relative_to(base_path))

        except Exception:
            pass

        return None
