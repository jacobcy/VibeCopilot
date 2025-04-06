"""
OpenAI API客户端
提供与OpenAI API交互的功能
"""

import logging
import os
from typing import Any, Dict, List, Optional

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from adapters.content_parser.utils.api_client import BaseAPIClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAPIClient):
    """OpenAI API客户端"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化OpenAI客户端

        Args:
            model: 使用的OpenAI模型名称
        """
        super().__init__(model)
        self.api_key = self._get_api_key()
        self.api_base = self._get_api_base()

        # 初始化OpenAI客户端
        openai.api_key = self.api_key
        if self.api_base:
            openai.api_base = self.api_base

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def parse_content(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用OpenAI API解析内容

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            Dict: 解析结果
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )

            # 提取结果
            result_text = response.choices[0].message.content.strip()

            # 处理JSON响应
            return self.handle_response(result_text)

        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise

    def _get_api_key(self) -> str:
        """获取OpenAI API密钥

        Returns:
            str: API密钥
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # 尝试从.env文件读取
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.strip().startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1].strip('"').strip("'")
                            break
            except:
                pass

        if not api_key:
            raise ValueError("未找到OpenAI API密钥，请设置环境变量OPENAI_API_KEY")

        return api_key

    def _get_api_base(self) -> Optional[str]:
        """获取OpenAI API基础URL

        Returns:
            str: API基础URL
        """
        return os.environ.get("OPENAI_API_BASE")
