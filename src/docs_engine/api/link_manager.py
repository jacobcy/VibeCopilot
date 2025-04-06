"""
链接管理器模块

提供文档和块之间链接的创建、检索和删除功能
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from src.docs_engine.storage import StorageEngine
from src.models.db.docs_engine import Link


class LinkManager:
    """链接管理器

    提供链接的高级操作接口
    """

    def __init__(self, storage_engine: Optional[StorageEngine] = None):
        """初始化

        Args:
            storage_engine: 存储引擎实例，如果为None则创建默认实例
        """
        self.storage = storage_engine or StorageEngine()

    def create_link(
        self,
        source_doc_id: str,
        target_doc_id: str,
        source_block_id: Optional[str] = None,
        target_block_id: Optional[str] = None,
        text: Optional[str] = None,
    ) -> Link:
        """创建链接

        Args:
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID（可选）
            target_block_id: 目标块ID（可选）
            text: 链接文本（可选）

        Returns:
            创建的Link对象
        """
        return self.storage.create_link(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            source_block_id=source_block_id,
            target_block_id=target_block_id,
            text=text,
        )

    def delete_link(self, link_id: str) -> bool:
        """删除链接

        Args:
            link_id: 链接ID

        Returns:
            是否删除成功
        """
        return self.storage.delete_link(link_id)

    def get_document_links(self, doc_id: str) -> Dict[str, List[Link]]:
        """获取文档的所有链接

        Args:
            doc_id: 文档ID

        Returns:
            包含入链和出链的字典
        """
        return {
            "incoming": self.storage.get_incoming_links(doc_id),
            "outgoing": self.storage.get_outgoing_links(doc_id),
        }

    def get_block_links(self, block_id: str) -> Dict[str, List[Link]]:
        """获取块的所有链接

        Args:
            block_id: 块ID

        Returns:
            包含入链和出链的字典
        """
        incoming, outgoing = self.storage.get_block_links(block_id)
        return {"incoming": incoming, "outgoing": outgoing}

    def parse_markdown_links(self, content: str, source_doc_id: str) -> List[Dict[str, Any]]:
        """解析Markdown内容中的链接

        Args:
            content: Markdown内容
            source_doc_id: 源文档ID

        Returns:
            解析出的链接信息列表
        """
        import re

        # 匹配 [[doc-id]] 或 [[doc-id#block-id]] 或 [[doc-id|显示文本]]
        pattern = r"\[\[(doc-[a-zA-Z0-9-]+)(?:#(blk-[a-zA-Z0-9-]+))?(?:\|(.*?))?\]\]"

        links = []
        for match in re.finditer(pattern, content):
            target_doc_id = match.group(1)
            target_block_id = match.group(2)
            display_text = match.group(3)

            links.append(
                {
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "target_doc_id": target_doc_id,
                    "target_block_id": target_block_id,
                    "text": display_text,
                }
            )

        return links

    def process_document_links(self, doc_id: str, content: str) -> List[Link]:
        """处理文档内容中的链接

        解析内容中的链接，并在数据库中创建相应的链接关系

        Args:
            doc_id: 文档ID
            content: 文档内容

        Returns:
            创建的Link对象列表
        """
        # 解析内容中的链接
        parsed_links = self.parse_markdown_links(content, doc_id)

        created_links = []
        for link_info in parsed_links:
            # 创建链接
            link = self.create_link(
                source_doc_id=doc_id,
                target_doc_id=link_info["target_doc_id"],
                target_block_id=link_info["target_block_id"],
                text=link_info["text"],
            )
            created_links.append(link)

        return created_links

    def process_block_links(self, block_id: str, document_id: str, content: str) -> List[Link]:
        """处理块内容中的链接

        解析块内容中的链接，并在数据库中创建相应的链接关系

        Args:
            block_id: 块ID
            document_id: 文档ID
            content: 块内容

        Returns:
            创建的Link对象列表
        """
        # 解析内容中的链接
        parsed_links = self.parse_markdown_links(content, document_id)

        created_links = []
        for link_info in parsed_links:
            # 创建链接
            link = self.create_link(
                source_doc_id=document_id,
                source_block_id=block_id,
                target_doc_id=link_info["target_doc_id"],
                target_block_id=link_info["target_block_id"],
                text=link_info["text"],
            )
            created_links.append(link)

        return created_links

    def analyze_document_graph(self, doc_id: str, depth: int = 1) -> Dict[str, Any]:
        """分析文档图谱

        Args:
            doc_id: 文档ID
            depth: 分析深度，默认为1（直接相邻文档）

        Returns:
            包含图谱信息的字典
        """
        if depth < 1:
            return {"nodes": [], "edges": []}

        # 分析第一层
        nodes = {}
        edges = []

        # 添加中心节点
        nodes[doc_id] = {"id": doc_id, "distance": 0}

        # 处理出链
        outgoing_links = self.storage.get_outgoing_links(doc_id)
        for link in outgoing_links:
            target_id = link.target_doc_id
            if target_id not in nodes:
                nodes[target_id] = {"id": target_id, "distance": 1}

            edges.append({"source": doc_id, "target": target_id, "id": link.id, "text": link.text})

        # 处理入链
        incoming_links = self.storage.get_incoming_links(doc_id)
        for link in incoming_links:
            source_id = link.source_doc_id
            if source_id not in nodes:
                nodes[source_id] = {"id": source_id, "distance": 1}

            edges.append({"source": source_id, "target": doc_id, "id": link.id, "text": link.text})

        # 如果需要更深的分析
        if depth > 1:
            next_level_ids = [node_id for node_id, node in nodes.items() if node["distance"] == 1]

            for next_id in next_level_ids:
                # 递归分析下一层，深度减1
                sub_graph = self.analyze_document_graph(next_id, depth - 1)

                # 合并节点
                for node_id, node in sub_graph["nodes"].items():
                    if node_id not in nodes:
                        # 调整距离
                        node["distance"] += 1
                        nodes[node_id] = node

                # 合并边
                for edge in sub_graph["edges"]:
                    # 检查边是否已存在
                    if not any(
                        e["source"] == edge["source"] and e["target"] == edge["target"]
                        for e in edges
                    ):
                        edges.append(edge)

        return {"nodes": list(nodes.values()), "edges": edges}
