"""
OpenAI API接口
提供与OpenAI API交互的客户端类
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API客户端"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化OpenAI客户端

        Args:
            model: 使用的OpenAI模型名称
        """
        self.model = model
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

            # 提取JSON部分
            try:
                # 尝试直接解析整个文本
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果失败，尝试提取JSON部分（通常被```json和```包围）
                import re

                json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
                matches = re.findall(json_pattern, result_text)

                if matches:
                    try:
                        result = json.loads(matches[0])
                    except json.JSONDecodeError:
                        logger.error("无法解析提取的JSON内容")
                        raise ValueError("无法解析AI生成的JSON内容")
                else:
                    logger.error("响应中找不到JSON内容")
                    raise ValueError("响应中找不到有效的JSON内容")

            return result

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
