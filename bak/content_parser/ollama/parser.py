"""
Ollama 解析器实现

定义 Ollama 内容解析器的核心类，使用 Ollama 服务解析 Markdown 文档和规则文件
"""

import logging
import subprocess
from typing import Any, Dict

from adapters.content_parser.base_parser import ContentParser
from adapters.content_parser.ollama.document_parser import parse_document
from adapters.content_parser.ollama.generic_parser import parse_generic
from adapters.content_parser.ollama.rule_parser import parse_rule

logger = logging.getLogger(__name__)


class OllamaParser(ContentParser):
    """Ollama内容解析器"""

    def __init__(self, model: str = "mistral", content_type: str = "generic"):
        """初始化解析器

        Args:
            model: 使用的Ollama模型
            content_type: 内容类型 ("rule", "document", "generic")
        """
        super().__init__(model, content_type)

    def parse_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """使用Ollama解析内容

        Args:
            content: 文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的结构
        """
        try:
            # 根据内容类型选择不同的解析方法
            if self.content_type == "rule":
                result = parse_rule(content, context, self.model)
            elif self.content_type == "document":
                result = parse_document(content, context, self.model)
            else:
                result = parse_generic(content, context, self.model)

            # 添加路径信息
            if context and "path" not in result:
                result["path"] = context

            # 确保内容字段存在
            if "content" not in result:
                result["content"] = content

            return result

        except Exception as e:
            logger.error(f"解析内容失败: {e}")
            print(f"解析内容失败: {e}")
            return self._get_default_result(context)

    def _get_default_result(self, context: str = "") -> Dict[str, Any]:
        """生成默认的解析结果

        Args:
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 默认的解析结果结构
        """
        if self.content_type == "rule":
            return {
                "id": context.split("/")[-1].split(".")[0] if context else "unknown",
                "name": "未解析规则",
                "type": "manual",
                "description": "解析失败时创建的默认规则",
                "globs": [],
                "always_apply": False,
                "items": [],
                "examples": [],
                "path": context,
            }
        elif self.content_type == "document":
            return {
                "id": context.split("/")[-1].split(".")[0] if context else "unknown",
                "title": "未解析文档",
                "description": "解析失败时创建的默认文档",
                "blocks": [],
                "path": context,
            }
        else:
            return {
                "id": context.split("/")[-1].split(".")[0] if context else "unknown",
                "title": "未解析内容",
                "content": "",
                "path": context,
            }
