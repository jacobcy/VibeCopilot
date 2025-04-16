"""
向量存储接口测试模块

测试向量存储抽象基类及其功能
"""

import os

# 添加项目根目录到Python路径
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.vector.vector_store import VectorStore


class TestVectorStore:
    """测试向量存储抽象基类"""

    def test_initialization(self):
        """测试初始化"""

        # 由于VectorStore是抽象类，我们创建一个简单实现来测试
        class TestStore(VectorStore):
            async def store(self, texts, metadata=None, folder=None):
                return ["1", "2", "3"][: len(texts)]

            async def search(self, query, limit=5, filter_dict=None):
                return [{"id": "1", "content": "test", "metadata": {}}]

            async def delete(self, ids):
                return True

            async def update(self, id, text, metadata=None):
                return True

            async def get(self, id):
                return {"id": id, "content": "test content", "metadata": {}}

        # 测试默认配置
        store = TestStore()
        assert store.config == {}

        # 测试自定义配置
        config = {"test_param": "value", "model": "test-model"}
        store = TestStore(config)
        assert store.config == config
        assert store.config.get("test_param") == "value"

    def test_abstract_methods(self):
        """测试抽象方法定义"""
        # 验证所有必需的抽象方法
        abstract_methods = VectorStore.__abstractmethods__
        assert "store" in abstract_methods
        assert "search" in abstract_methods
        assert "delete" in abstract_methods
        assert "update" in abstract_methods
        assert "get" in abstract_methods

    def test_implementation_requirements(self):
        """测试实现要求"""
        # 尝试直接实例化抽象类应该失败
        with pytest.raises(TypeError):
            VectorStore()

        # 测试缺少方法的实现也应该失败
        class IncompleteStore(VectorStore):
            async def store(self, texts, metadata=None, folder=None):
                return ["1", "2", "3"][: len(texts)]

            # 缺少其他必需方法

        with pytest.raises(TypeError):
            IncompleteStore()
