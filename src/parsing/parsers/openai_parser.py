"""
OpenAI解析器兼容层

为了与现有代码兼容，提供与旧版API相同接口的兼容层。
新代码应直接使用LLMParser。
"""

import logging
from typing import Any, Dict, Optional

from src.parsing.parsers.llm_parser import LLMParser

logger = logging.getLogger(__name__)


class OpenAIParser(LLMParser):
    """
    OpenAI解析器兼容层

    为了与现有代码兼容提供的兼容层。新代码应直接使用LLMParser。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化OpenAI解析器兼容层

        Args:
            config: 配置参数
        """
        # 确保config中provider设置为openai
        config = config or {}
        config["provider"] = "openai"

        super().__init__(config)
