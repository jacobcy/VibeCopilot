"""
Basic Memory适配器集成测试

测试Basic Memory适配器与各种服务的集成情况
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.db.vector.memory_adapter import BasicMemoryAdapter
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager


@pytest.mark.integration
class TestBasicMemoryAdapterIntegration:
    """测试Basic Memory适配器与其他服务的集成"""

    @pytest.fixture
    def adapter(self):
        """创建测试用的适配器"""
        config = {"default_folder": "vibecopilot_test", "default_tags": "test,integration"}
        return BasicMemoryAdapter(config)

    @pytest.mark.asyncio
    @patch("src.memory.observation_manager.BasicMemoryAdapter")
    async def test_observation_manager_integration(self, mock_adapter_class, adapter):
        """测试与ObservationManager的集成"""
        # 配置模拟
        mock_adapter = MagicMock()
        # 创建一个异步方法的模拟
        async_store_mock = AsyncMock()
        async_store_mock.return_value = ["memory://test/observation1"]
        mock_adapter.store = async_store_mock

        async_search_mock = AsyncMock()
        async_search_mock.return_value = [{"permalink": "memory://test/observation1", "content": "测试观察", "metadata": {"title": "测试标题", "score": 0.9}}]
        mock_adapter.search = async_search_mock

        async_get_mock = AsyncMock()
        async_get_mock.return_value = {
            "permalink": "memory://test/observation1",
            "content": "测试观察详情",
            "metadata": {"title": "测试标题", "type": "generic", "timestamp": "2025-04-08T12:00:00", "score": 0.9},
        }
        mock_adapter.get = async_get_mock
        mock_adapter_class.return_value = mock_adapter

        # 创建ObservationManager实例
        manager = ObservationManager()

        # 测试记录观察
        content = "测试观察内容"
        metadata = {"source": "单元测试", "tags": "test", "title": "测试观察"}
        result = await manager.record_observation(content, metadata)

        # 验证结果
        assert result["permalink"] == "memory://test/observation1"
        mock_adapter.store.assert_called_once()

        # 测试搜索观察
        query_results = await manager.search_observations("测试")
        assert len(query_results) == 1
        assert query_results[0]["permalink"] == "memory://test/observation1"
        mock_adapter.search.assert_called_once()

        # 测试获取观察
        get_result = await manager.get_observation("memory://test/observation1")
        assert get_result["permalink"] == "memory://test/observation1"
        mock_adapter.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.memory.entity_manager.BasicMemoryAdapter")
    async def test_entity_manager_integration(self, mock_adapter_class, adapter):
        """测试与EntityManager的集成"""
        # 配置模拟
        mock_adapter = MagicMock()
        # 创建一个异步方法的模拟
        async_store_mock = AsyncMock()
        async_store_mock.return_value = ["memory://test/entity1"]
        mock_adapter.store = async_store_mock

        async_search_mock = AsyncMock()
        async_search_mock.return_value = [
            {"permalink": "memory://test/entity1", "content": "测试实体", "metadata": {"title": "实体1", "score": 0.9, "type": "concept"}}
        ]
        mock_adapter.search = async_search_mock

        async_get_mock = AsyncMock()
        async_get_mock.return_value = {
            "permalink": "memory://test/entity1",
            "content": "测试实体详情",
            "metadata": {"title": "实体1", "type": "concept", "score": 0.9},
        }
        mock_adapter.get = async_get_mock
        mock_adapter_class.return_value = mock_adapter

        # 创建EntityManager实例
        manager = EntityManager()

        # 测试创建实体
        entity_type = "concept"
        properties = {"name": "测试实体", "description": "这是一个测试实体", "key": "value"}
        result = await manager.create_entity(entity_type, properties)

        # 验证结果
        assert result["permalink"] == "memory://test/entity1"
        mock_adapter.store.assert_called_once()

        # 测试搜索实体
        query_results = await manager.search_entities("测试", entity_type="concept")
        assert len(query_results) == 1
        assert query_results[0]["permalink"] == "memory://test/entity1"
        mock_adapter.search.assert_called_once()

        # 测试获取实体
        get_result = await manager.get_entity("memory://test/entity1")
        assert get_result["permalink"] == "memory://test/entity1"
        mock_adapter.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.memory.relation_manager.BasicMemoryAdapter")
    async def test_relation_manager_integration(self, mock_adapter_class, adapter):
        """测试与RelationManager的集成"""
        # 配置模拟
        mock_adapter = MagicMock()
        # 创建一个异步方法的模拟
        async_store_mock = AsyncMock()
        async_store_mock.return_value = ["memory://test/relation1"]
        mock_adapter.store = async_store_mock

        async_search_mock = AsyncMock()
        async_search_mock.return_value = [
            {
                "permalink": "memory://test/relation1",
                "content": "实体A[关系]实体B",
                "metadata": {"title": "关系1", "score": 0.9, "type": "relation", "source_id": "entity_a", "target_id": "entity_b"},
            }
        ]
        mock_adapter.search = async_search_mock

        async_get_mock = AsyncMock()
        async_get_mock.return_value = {
            "permalink": "memory://test/relation1",
            "content": "实体A[关系]实体B详情",
            "metadata": {"title": "关系1", "type": "relation", "score": 0.9, "source_id": "entity_a", "target_id": "entity_b"},
        }
        mock_adapter.get = async_get_mock
        mock_adapter_class.return_value = mock_adapter

        # 创建RelationManager实例
        manager = RelationManager()

        # 测试创建关系
        source_id = "entity_a"
        target_id = "entity_b"
        relation_type = "关系"
        properties = {"description": "这是一个测试关系", "key": "value"}
        result = await manager.create_relation(source_id, target_id, relation_type, properties)

        # 验证结果
        assert result["permalink"] == "memory://test/relation1"
        mock_adapter.store.assert_called_once()

        # 测试获取关系
        query_results = await manager.get_relations("entity_a")
        assert len(query_results) == 1
        assert query_results[0]["permalink"] == "memory://test/relation1"
        mock_adapter.search.assert_called_once()
