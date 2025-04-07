"""
规则处理器

专门用于处理规则文件的处理器。
"""

import os
from glob import glob
from typing import Any, Dict, List, Optional

from src.parsing.parser_factory import create_parser


class RuleProcessor:
    """
    规则处理器

    提供解析和处理规则文件的专门功能。
    """

    def __init__(self, backend="openai", config=None):
        """
        初始化规则处理器

        Args:
            backend: 解析后端，如'openai'、'ollama'、'regex'
            config: 配置参数
        """
        self.backend = backend
        self.config = config or {}

        # 创建解析器
        self.parser = create_parser("rule", backend, config)

    def process_rule_text(self, content: str) -> Dict[str, Any]:
        """
        处理规则文本

        Args:
            content: 规则文本内容

        Returns:
            处理结果
        """
        # 解析规则内容
        result = self.parser.parse_text(content, "rule")

        # 验证规则结构
        if not self._validate_rule_structure(result):
            result["validation"] = {"valid": False, "errors": ["Rule structure is invalid"]}
        else:
            result["validation"] = {"valid": True, "errors": []}

        return result

    def process_rule_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理规则文件

        Args:
            file_path: 规则文件路径

        Returns:
            处理结果
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 处理规则文本
        result = self.process_rule_text(content)

        # 添加文件信息
        result["file_info"] = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "directory": os.path.dirname(file_path),
        }

        return result

    def process_rule_directory(
        self, directory_path: str, pattern="**/*.mdc"
    ) -> List[Dict[str, Any]]:
        """
        处理规则目录

        Args:
            directory_path: 规则目录路径
            pattern: 文件匹配模式

        Returns:
            处理结果列表
        """
        # 检查目录是否存在
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return [{"success": False, "error": f"Directory not found: {directory_path}"}]

        # 查找规则文件
        rule_files = glob(os.path.join(directory_path, pattern), recursive=True)

        # 处理每个规则文件
        results = []
        for file_path in rule_files:
            result = self.process_rule_file(file_path)
            results.append(result)

        return results

    def extract_rule_metadata(self, rule_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取规则元数据

        Args:
            rule_result: 规则处理结果

        Returns:
            规则元数据
        """
        metadata = {
            "title": rule_result.get("title", ""),
            "type": rule_result.get("front_matter", {}).get("type", ""),
            "description": rule_result.get("front_matter", {}).get("description", ""),
            "tags": rule_result.get("front_matter", {}).get("tags", "").split(",")
            if rule_result.get("front_matter", {}).get("tags")
            else [],
            "valid": rule_result.get("validation", {}).get("valid", False),
        }

        # 添加文件信息（如果有）
        if "file_info" in rule_result:
            metadata["file_path"] = rule_result["file_info"]["path"]
            metadata["file_name"] = rule_result["file_info"]["name"]
            metadata["directory"] = rule_result["file_info"]["directory"]

        return metadata

    def _validate_rule_structure(self, rule_result: Dict[str, Any]) -> bool:
        """
        验证规则结构

        Args:
            rule_result: 规则处理结果

        Returns:
            规则结构是否有效
        """
        # 检查必要的字段
        if not rule_result.get("title"):
            return False

        # 检查Front Matter
        front_matter = rule_result.get("front_matter", {})
        if not front_matter.get("type") or not front_matter.get("description"):
            return False

        return True
