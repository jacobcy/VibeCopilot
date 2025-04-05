"""引擎配置模块."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class EngineConfig(BaseModel):
    """引擎配置类.

    定义引擎运行所需的各项参数配置。
    """

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", description="用于生成文本嵌入的模型"
    )

    vector_store_path: str = Field(default="./vector_store", description="向量存储的路径")

    vector_store_type: Literal["chroma", "faiss", "milvus"] = Field(
        default="chroma", description="向量存储的类型"
    )

    model_adapter: Literal["openai", "anthropic", "llama", "gemini"] = Field(
        default="openai", description="模型适配器类型"
    )

    model_config: Dict[str, Any] = Field(default_factory=dict, description="模型特定配置")

    similarity_top_k: int = Field(default=5, description="检索结果数量", ge=1, le=100)

    similarity_threshold: float = Field(default=0.7, description="相似度阈值", ge=0.0, le=1.0)

    cache_enabled: bool = Field(default=True, description="是否启用缓存")

    cache_expiry: int = Field(default=3600, description="缓存过期时间（秒）", ge=0)

    debug_mode: bool = Field(default=False, description="是否启用调试模式")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="日志级别"
    )

    max_token_limit: int = Field(default=8000, description="最大令牌限制", ge=100)

    # Pydantic v2配置
    model_config = {"arbitrary_types_allowed": True, "validate_assignment": True}

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "EngineConfig":
        """从字典创建配置实例."""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return self.model_dump()
