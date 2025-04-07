"""
向量存储接口

定义向量存储的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class VectorStore(ABC):
    """
    向量存储接口

    定义了所有向量存储实现必须提供的方法。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储

        Args:
            config: 配置参数
        """
        self.config = config or {}

    @abstractmethod
    async def store(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        folder: Optional[str] = None,
    ) -> List[str]:
        """
        存储文本及其元数据

        Args:
            texts: 待存储的文本列表
            metadata: 文本对应的元数据列表
            folder: 存储文件夹

        Returns:
            存储后的文本ID或永久链接列表
        """
        pass

    @abstractmethod
    async def search(
        self, query: str, limit: int = 5, filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文本

        Args:
            query: 查询文本
            limit: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """
        删除文本

        Args:
            ids: 文本ID或永久链接列表

        Returns:
            删除是否成功
        """
        pass

    @abstractmethod
    async def update(self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新文本和元数据

        Args:
            id: 文本ID或永久链接
            text: 新文本
            metadata: 新元数据

        Returns:
            更新是否成功
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取文本

        Args:
            id: 文本ID或永久链接

        Returns:
            文本及其元数据
        """
        pass
