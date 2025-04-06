"""
块管理器模块

提供文档块的创建、检索、更新和删除功能
"""

from typing import Any, Dict, List, Optional, Union

from src.docs_engine.storage import StorageEngine
from src.models.db.docs_engine import Block, BlockType


class BlockManager:
    """块管理器

    提供块的高级操作接口
    """

    def __init__(self, storage_engine: Optional[StorageEngine] = None):
        """初始化

        Args:
            storage_engine: 存储引擎实例，如果为None则创建默认实例
        """
        self.storage = storage_engine or StorageEngine()

    def create_block(
        self,
        document_id: str,
        content: str,
        type=None,
        block_type: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        sequence: int = None,
    ) -> Block:
        """创建块

        Args:
            document_id: 文档ID
            content: 块内容
            block_type: 块类型
            metadata: 元数据（可选）

        Returns:
            创建的Block对象
        """
        # 处理兼容性
        if type is None and block_type is not None:
            type = block_type

        return self.storage.create_block(
            document_id=document_id,
            content=content,
            type=type,
            metadata=metadata,
            sequence=sequence,
        )

    def get_block(self, block_id: str) -> Optional[Block]:
        """获取块

        Args:
            block_id: 块ID

        Returns:
            Block对象或None
        """
        return self.storage.get_block(block_id)

    def update_block(
        self,
        block_id: str,
        content: Optional[str] = None,
        type=None,
        block_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sequence: int = None,
    ) -> Optional[Block]:
        """更新块

        Args:
            block_id: 块ID
            content: 新内容（可选）
            block_type: 新类型（可选）
            metadata: 新元数据（可选）

        Returns:
            更新后的Block对象或None
        """
        updates = {}

        if content is not None:
            updates["content"] = content

        if type is not None:
            updates["type"] = type
        elif block_type is not None:
            updates["type"] = block_type

        if sequence is not None:
            updates["order"] = sequence

        if metadata is not None:
            updates["metadata"] = metadata

        if not updates:
            return self.get_block(block_id)

        return self.storage.update_block(block_id, updates)

    def delete_block(self, block_id: str) -> bool:
        """删除块

        Args:
            block_id: 块ID

        Returns:
            是否删除成功
        """
        return self.storage.delete_block(block_id)

    def get_document_blocks(self, doc_id: str) -> List[Block]:
        """获取文档的所有块

        Args:
            doc_id: 文档ID

        Returns:
            Block对象列表
        """
        return self.storage.get_document_blocks(doc_id)

    def split_markdown_content(self, document_id: str, content: str) -> List[Block]:
        """将内容分割为多个块并添加到文档

        Args:
            document_id: 文档ID
            content: 要分割的内容

        Returns:
            创建的Block对象列表
        """
        blocks = []

        # 简单分割逻辑：按行分割，识别标题
        lines = content.split("\n")
        current_block = {"type": BlockType.TEXT, "content": ""}

        for line in lines:
            # 识别标题
            if line.startswith("# "):
                # 如果当前有内容，保存现有块
                if current_block["content"].strip():
                    block = self.create_block(
                        document_id=document_id,
                        content=current_block["content"].strip(),
                        block_type=current_block["type"],
                    )
                    blocks.append(block)

                # 创建标题块
                block = self.create_block(
                    document_id=document_id,
                    content=line.strip("# ").strip(),
                    type=BlockType.HEADING,
                    metadata={"level": 1},
                    sequence=len(blocks),
                )
                blocks.append(block)

                # 重置当前块
                current_block = {"type": BlockType.TEXT, "content": ""}

            # 识别代码块
            elif line.startswith("```"):
                # 如果已经在代码块中，结束代码块
                if current_block["type"] == BlockType.CODE:
                    # 从```python中提取语言
                    language = "text"
                    if "language" in current_block and current_block["language"]:
                        language = current_block["language"]

                    block = self.create_block(
                        document_id=document_id,
                        content=current_block["content"].strip(),
                        type=current_block["type"],
                        metadata={"language": language},
                        sequence=len(blocks),
                    )
                    blocks.append(block)
                    current_block = {"type": BlockType.TEXT, "content": ""}
                # 开始新代码块
                else:
                    # 如果当前有内容，保存现有块
                    if current_block["content"].strip():
                        block = self.create_block(
                            document_id=document_id,
                            content=current_block["content"].strip(),
                            type=current_block["type"],
                            sequence=len(blocks),
                        )
                        blocks.append(block)

                    # 提取语言信息
                    language = "text"
                    lang_marker = line.strip().lstrip("`").strip()
                    if lang_marker:
                        language = lang_marker

                    # 开始新代码块
                    current_block = {"type": BlockType.CODE, "content": "", "language": language}

            # 普通内容，添加到当前块
            else:
                current_block["content"] += line + "\n"

        # 保存最后一个块
        if current_block["content"].strip():
            kwargs = {
                "document_id": document_id,
                "content": current_block["content"].strip(),
                "type": current_block["type"],
                "sequence": len(blocks),
            }

            # 如果是代码块，添加语言信息
            if current_block["type"] == BlockType.CODE and "language" in current_block:
                kwargs["metadata"] = {"language": current_block["language"]}

            block = self.create_block(**kwargs)
            blocks.append(block)

        return blocks

    def reorder_blocks(self, doc_id: str, block_ids: List[str]) -> bool:
        """重新排序文档的块

        Args:
            doc_id: 文档ID
            block_ids: 按新顺序排列的块ID列表

        Returns:
            是否成功
        """
        return self.storage.reorder_blocks(doc_id, block_ids)
