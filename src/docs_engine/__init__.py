"""
动态文档系统

VibeCopilot的动态文档系统提供以下功能：
1. 文档创建、更新和删除
2. 块级别的内容管理
3. 文档间链接关系处理
4. Markdown导入与渲染
5. 文档搜索与发现
"""

from .api.block_manager import BlockManager
from .api.document_engine import DocumentEngine
from .api.link_manager import LinkManager
from .tools import MarkdownImporter

__all__ = ["DocumentEngine", "BlockManager", "LinkManager", "MarkdownImporter"]
