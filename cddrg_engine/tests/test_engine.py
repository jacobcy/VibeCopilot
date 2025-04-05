"""引擎核心模块测试."""

from unittest.mock import MagicMock, patch

import pytest

from cddrg_engine.config import EngineConfig
from cddrg_engine.engine import Engine


def test_engine_init():
    """测试引擎初始化."""
    engine = Engine()
    assert isinstance(engine.config, EngineConfig)
    assert engine._initialized is False

    custom_config = EngineConfig(embedding_model="custom-model", debug_mode=True, log_level="DEBUG")
    engine = Engine(config=custom_config)
    assert engine.config.embedding_model == "custom-model"
    assert engine.config.debug_mode is True
    assert engine.config.log_level == "DEBUG"


def test_get_status():
    """测试获取引擎状态."""
    engine = Engine()
    status = engine.get_status()

    assert isinstance(status, dict)
    assert "initialized" in status
    assert "uptime_seconds" in status
    assert "config" in status
    assert "version" in status
    assert status["initialized"] is False
    assert isinstance(status["uptime_seconds"], float)
    assert status["uptime_seconds"] >= 0
    assert status["version"] == "0.1.0"


@patch("cddrg_engine.engine.Engine._initialize_vector_store")
@patch("cddrg_engine.engine.Engine._initialize_model_adapter")
def test_ensure_initialized(mock_init_vector, mock_init_model):
    """测试确保引擎初始化."""
    engine = Engine()
    assert engine._initialized is False

    # 调用需要确保初始化的方法
    engine.add_knowledge("测试内容")

    # 验证初始化方法被调用
    mock_init_vector.assert_called_once()
    mock_init_model.assert_called_once()
    assert engine._initialized is True

    # 再次调用不应触发初始化
    engine.add_knowledge("测试内容2")
    assert mock_init_vector.call_count == 1
    assert mock_init_model.call_count == 1


@patch("cddrg_engine.engine.Engine._ensure_initialized")
def test_add_knowledge(mock_ensure_init):
    """测试添加知识."""
    engine = Engine()
    knowledge_id = engine.add_knowledge(
        content="测试知识内容", metadata={"type": "test", "source": "unit-test"}
    )

    # 确保初始化被调用
    mock_ensure_init.assert_called_once()
    # 返回值应是字符串ID
    assert isinstance(knowledge_id, str)


@patch("cddrg_engine.engine.Engine._ensure_initialized")
def test_generate_rule(mock_ensure_init):
    """测试生成规则."""
    engine = Engine()
    rule = engine.generate_rule(context="测试上下文", task="测试任务", metadata={"category": "test"})

    # 确保初始化被调用
    mock_ensure_init.assert_called_once()
    # 返回值应是包含必要字段的字典
    assert isinstance(rule, dict)
    assert "id" in rule
    assert "content" in rule
    assert "metadata" in rule
    assert "created_at" in rule
    assert rule["metadata"]["category"] == "test"


@patch("cddrg_engine.engine.Engine._ensure_initialized")
def test_query(mock_ensure_init):
    """测试查询知识库."""
    engine = Engine()
    results = engine.query(query="测试查询", filters={"type": "test"})

    # 确保初始化被调用
    mock_ensure_init.assert_called_once()
    # 返回值应是列表
    assert isinstance(results, list)
