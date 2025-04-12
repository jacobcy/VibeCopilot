"""
工作流处理器

专门用于处理和验证工作流内容的处理器。
"""

import json
from typing import Any, Dict, Optional

from src.core.exceptions import ValidationError
from src.parsing.parser_factory import create_parser
from src.validation import workflow_validation


class WorkflowProcessor:
    """工作流处理器，用于解析和验证工作流内容"""

    def __init__(self, backend="openai", config=None):
        """初始化工作流处理器

        Args:
            backend: 解析后端，如'openai'、'ollama'
            config: 配置参数
        """
        self.backend = backend
        self.config = config or {}

        # 创建解析器
        self.parser = create_parser("workflow", backend, config)

    async def parse_workflow_rule(self, rule_content: str) -> Dict[str, Any]:
        """
        解析规则文件中的工作流内容

        Args:
            rule_content: 规则文件内容

        Returns:
            解析后的工作流结果字典
        """
        try:
            # 使用解析器解析内容
            result = await self.parser.parse_text(rule_content, "workflow")

            if not result.get("success", False):
                return {"success": False, "error": result.get("error", "Failed to parse workflow"), "content_type": "workflow"}

            # 获取工作流数据
            workflow_data = result.get("content", {})

            # 验证工作流结构
            try:
                # 使用验证模块验证工作流
                workflow_validation.validate_workflow(workflow_data)

                return {"success": True, "content_type": "workflow", "content": workflow_data}

            except ValidationError as e:
                return {"success": False, "error": str(e), "content_type": "workflow", "content": workflow_data}

        except Exception as e:
            return {"success": False, "error": str(e), "content_type": "workflow"}

    async def parse_workflow(self, content: str) -> Dict[str, Any]:
        """
        解析工作流内容

        Args:
            content: 工作流内容字符串

        Returns:
            解析后的工作流结果字典
        """
        # 直接复用同样的解析逻辑
        return await self.parse_workflow_rule(content)
