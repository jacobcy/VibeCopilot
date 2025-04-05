"""引擎配置模块测试."""

import pytest
from pydantic import ValidationError

from cddrg_engine.config import EngineConfig


def test_default_config():
    """测试默认配置."""
    config = EngineConfig()

    assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.vector_store_path == "./vector_store"
    assert config.vector_store_type == "chroma"
    assert config.model_adapter == "openai"
    assert config.similarity_top_k == 5
    assert config.similarity_threshold == 0.7
    assert config.cache_enabled is True
    assert config.debug_mode is False
    assert config.log_level == "INFO"


def test_custom_config():
    """测试自定义配置."""
    custom_config = {
        "embedding_model": "custom-embedding-model",
        "vector_store_path": "/custom/path",
        "vector_store_type": "faiss",
        "model_adapter": "anthropic",
        "similarity_top_k": 10,
        "similarity_threshold": 0.8,
        "cache_enabled": False,
        "debug_mode": True,
        "log_level": "DEBUG",
    }

    config = EngineConfig(**custom_config)

    assert config.embedding_model == "custom-embedding-model"
    assert config.vector_store_path == "/custom/path"
    assert config.vector_store_type == "faiss"
    assert config.model_adapter == "anthropic"
    assert config.similarity_top_k == 10
    assert config.similarity_threshold == 0.8
    assert config.cache_enabled is False
    assert config.debug_mode is True
    assert config.log_level == "DEBUG"


def test_from_dict():
    """测试从字典创建配置."""
    config_dict = {
        "embedding_model": "test-model",
        "vector_store_type": "milvus",
        "log_level": "WARNING",
    }

    config = EngineConfig.from_dict(config_dict)

    assert config.embedding_model == "test-model"
    assert config.vector_store_type == "milvus"
    assert config.log_level == "WARNING"
    # 确认默认值
    assert config.vector_store_path == "./vector_store"
    assert config.model_adapter == "openai"


def test_to_dict():
    """测试转换为字典."""
    config = EngineConfig(embedding_model="test-model", vector_store_type="faiss", debug_mode=True)

    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)
    assert config_dict["embedding_model"] == "test-model"
    assert config_dict["vector_store_type"] == "faiss"
    assert config_dict["debug_mode"] is True


def test_validation():
    """测试配置验证."""
    # 无效的向量存储类型
    with pytest.raises(ValidationError):
        EngineConfig(vector_store_type="invalid_type")

    # 无效的模型适配器
    with pytest.raises(ValidationError):
        EngineConfig(model_adapter="invalid_adapter")

    # 无效的相似度阈值范围
    with pytest.raises(ValidationError):
        EngineConfig(similarity_threshold=1.5)

    # 无效的日志级别
    with pytest.raises(ValidationError):
        EngineConfig(log_level="VERBOSE")
