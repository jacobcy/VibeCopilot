"""
向量存储抽象基类

定义了向量存储接口的抽象基类。
"""

import abc
from typing import Any, Dict, List, Optional, Union


class VectorStore(abc.ABC):
    """
    向量存储抽象基类

    所有向量存储实现都应继承此类并实现其方法。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化向量存储

        Args:
            config: 配置参数
        """
        self.config = config or {}

    @abc.abstractmethod
    async def store(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        folder: Optional[str] = None,
    ) -> List[str]:
        """
        存储文本及元数据到向量库

        Args:
            texts: 要存储的文本列表
            metadata: 每个文本对应的元数据
            folder: 存储文件夹

        Returns:
            存储后的永久链接列表
        """
        pass

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索向量库

        Args:
            query: 搜索查询
            limit: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        pass

    @abc.abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            id: 永久链接

        Returns:
            文档内容和元数据
        """
        pass

    @abc.abstractmethod
    async def update(self, id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        更新文档

        Args:
            id: 永久链接
            content: 新内容
            metadata: 新元数据

        Returns:
            更新是否成功
        """
        pass

    @abc.abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 永久链接列表

        Returns:
            删除是否成功
        """
        pass

    @abc.abstractmethod
    async def list_folders(self) -> List[str]:
        """
        列出所有文件夹

        Returns:
            文件夹列表
        """
        pass

    @abc.abstractmethod
    async def list_documents(self, folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文件夹中的所有文档

        Args:
            folder: 文件夹名称，如果为None则列出所有文件夹中的文档

        Returns:
            文档列表
        """
        pass

    @abc.abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接是否正常

        Returns:
            测试结果
        """
        pass
