"""
Basic Memory适配器测试模块

测试Basic Memory适配器的功能和接口
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.vector.memory_adapter import BasicMemoryAdapter


class TestBasicMemoryAdapter:
    """测试Basic Memory适配器"""

    def test_initialization(self):
        """测试初始化"""
        # 测试默认配置
        adapter = BasicMemoryAdapter()
        assert adapter.config == {}
        assert adapter.default_folder == "vibecopilot"  # 默认文件夹
        assert adapter.default_tags == "vibecopilot"  # 默认标签

        # 测试自定义配置
        config = {"default_folder": "custom_folder", "default_tags": "custom_tags"}
        adapter = BasicMemoryAdapter(config)
        assert adapter.default_folder == "custom_folder"
        assert adapter.default_tags == "custom_tags"

    @pytest.mark.asyncio
    async def test_store(self):
        """测试存储功能"""
        adapter = BasicMemoryAdapter()

        # 测试基本存储功能
        texts = ["测试文本1", "测试文本2"]
        metadata = [{"title": "文档1"}, {"title": "文档2"}]

        # 捕获print输出
        with patch("builtins.print") as mock_print:
            permalinks = await adapter.store(texts, metadata)

            # 验证结果
            assert len(permalinks) == 2
            assert all("memory://" in link for link in permalinks)
            assert "文档1" in permalinks[0]
            assert "文档2" in permalinks[1]

            # 验证打印输出
            assert mock_print.call_count == 2

    @pytest.mark.asyncio
    async def test_store_metadata_validation(self):
        """测试存储元数据验证"""
        adapter = BasicMemoryAdapter()

        # 测试元数据列表长度不匹配
        texts = ["测试文本1", "测试文本2"]
        metadata = [{"title": "文档1"}]  # 只有一个元数据项

        with pytest.raises(ValueError) as excinfo:
            await adapter.store(texts, metadata)

        assert "Metadata list length must match texts list length" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_search(self):
        """测试搜索功能"""
        adapter = BasicMemoryAdapter()

        # 捕获print输出
        with patch("builtins.print") as mock_print:
            results = await adapter.search("测试查询", limit=2)

            # 验证结果
            assert len(results) == 2  # 限制为2个结果
            assert all("permalink" in result for result in results)
            assert all("content" in result for result in results)
            assert all("metadata" in result for result in results)

            # 验证分数排序
            assert results[0]["metadata"]["score"] > results[1]["metadata"]["score"]

            # 验证打印输出
            mock_print.assert_called_once_with("Searching for '测试查询' with limit 2")

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除功能"""
        adapter = BasicMemoryAdapter()

        # 捕获print输出
        with patch("builtins.print") as mock_print:
            success = await adapter.delete(["memory://test/doc1", "memory://test/doc2"])

            # 验证结果
            assert success is True

            # 验证打印输出
            assert mock_print.call_count == 2

    @pytest.mark.asyncio
    async def test_update(self):
        """测试更新功能"""
        adapter = BasicMemoryAdapter()

        # 捕获print输出
        with patch("builtins.print") as mock_print:
            success = await adapter.update("memory://test/doc", "更新后的内容", {"title": "新标题"})

            # 验证结果
            assert success is True

            # 验证打印输出
            mock_print.assert_called_once_with("Updated text with permalink 'memory://test/doc'")

    @pytest.mark.asyncio
    async def test_get(self):
        """测试获取功能"""
        adapter = BasicMemoryAdapter()

        # 捕获print输出
        with patch("builtins.print") as mock_print:
            result = await adapter.get("memory://test/test_doc")

            # 验证结果
            assert result is not None
            assert result["permalink"] == "memory://test/test_doc"
            assert "content" in result
            assert "metadata" in result
            assert "title" in result["metadata"]

            # 验证打印输出
            mock_print.assert_called_once_with("Getting text with permalink 'memory://test/test_doc'")
