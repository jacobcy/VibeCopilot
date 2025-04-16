"""
OpenAI service for interacting with OpenAI API.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

import numpy as np
import openai
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.core.config.manager import get_config

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI service class for making API calls."""

    def __init__(self):
        """Initialize OpenAI service."""
        config_manager = get_config()
        self.api_key = config_manager.get("ai.openai.api_key")

        if not self.api_key:
            load_dotenv()
            self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not found in config or environment variables")

        self.client = OpenAI(api_key=self.api_key)

        # 从配置获取模型和服务名称
        self.chat_model = config_manager.get("ai.chat_model", "gpt-4o-mini")
        self.embedding_model = config_manager.get("ai.embedding_model", "text-embedding-ada-002")
        # 从配置获取嵌入维度
        self.embedding_dimensions = config_manager.get("ai.embedding_dimension", 384)

    async def chat_completion(
        self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs: Any
    ) -> ChatCompletion:
        """
        Make an asynchronous chat completion request to OpenAI API.

        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API

        Returns:
            ChatCompletion object containing the API response

        Raises:
            Exception: If the API call fails
        """
        try:
            logger.debug(f"Making chat completion request with {len(messages)} messages")
            # Run the synchronous API call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.chat_model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
                ),
            )
            logger.debug("Chat completion request successful")
            return response
        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {str(e)}")
            raise Exception(f"OpenAI API call failed: {str(e)}")

    async def create_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        为文本创建嵌入向量，并降维到指定维度

        Args:
            texts: 单个文本字符串或文本列表

        Returns:
            降维后的嵌入向量列表（维度由self.embedding_dimensions指定）

        Raises:
            Exception: 如果API调用失败
        """
        # 确保文本是列表形式
        if isinstance(texts, str):
            texts = [texts]

        try:
            logger.debug(f"创建嵌入向量, 文本数量: {len(texts)}")
            # 运行同步API调用 - 注意：OpenAI API可能不允许直接指定输出维度，降维在后面处理
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.embeddings.create(model=self.embedding_model, input=texts),
            )
            logger.debug("嵌入向量创建成功")

            # 提取原始嵌入向量
            original_embeddings = [data.embedding for data in response.data]
            original_dim = len(original_embeddings[0]) if original_embeddings else 0

            # 检查配置的维度是否有效
            target_dim = self.embedding_dimensions
            if target_dim <= 0 or target_dim > original_dim:
                logger.warning(
                    f"配置的嵌入维度 ({target_dim}) 无效或大于原始维度 ({original_dim}). " f"将使用原始维度 {original_dim}. 请检查 .env 文件中的 AI_EMBEDDING_DIMENSION."
                )
                target_dim = original_dim  # 如果配置无效，则不进行降维
            elif target_dim == original_dim:
                logger.debug(f"目标维度与原始维度相同 ({target_dim})，无需降维。")
                return original_embeddings  # 无需降维

            # 执行降维处理
            reduced_embeddings = []
            for emb in original_embeddings:
                # 简单截断法 - 只保留前N个维度
                reduced_emb = emb[:target_dim]
                # 重新归一化向量，确保向量长度为1
                norm = np.linalg.norm(reduced_emb)
                if norm > 0:  # Avoid division by zero
                    reduced_emb = list(np.array(reduced_emb) / norm)
                else:
                    # Handle zero vector if necessary, maybe return as is or log warning
                    logger.warning("Encountered zero vector during embedding normalization.")
                    reduced_emb = list(reduced_emb)  # Keep as zero vector
                reduced_embeddings.append(reduced_emb)

            logger.debug(f"嵌入向量已降维: {original_dim} -> {target_dim}")
            return reduced_embeddings

        except openai.RateLimitError as e:
            logger.error(f"创建嵌入向量时达到速率限制: {str(e)}")
            raise
        except openai.APIError as e:
            logger.error(f"创建嵌入向量时OpenAI API错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"创建嵌入向量时出现意外错误: {str(e)}")
            raise Exception(f"创建嵌入向量失败: {str(e)}")

    def get_embedding_model_name(self) -> str:
        """
        获取当前配置的嵌入模型名称

        Returns:
            嵌入模型名称
        """
        return self.embedding_model
