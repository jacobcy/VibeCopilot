"""
规则解析器基类
定义规则解析器接口
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import frontmatter

logger = logging.getLogger(__name__)


class RuleParser(ABC):
    """规则解析器基类"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化解析器

        Args:
            model: 使用的模型名称
        """
        self.model = model

    def parse_rule_file(self, file_path: str) -> Dict[str, Any]:
        """解析规则文件

        Args:
            file_path: 规则文件路径

        Returns:
            Dict: 解析后的规则结构
        """
        # 读取规则文件
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 优先尝试解析Front Matter
            try:
                post = frontmatter.load(file_path)
                metadata = post.metadata

                # 如果有有效的Front Matter数据，直接返回
                if metadata and self._is_valid_metadata(metadata):
                    metadata["content"] = post.content
                    metadata["id"] = metadata.get("id", Path(file_path).stem)
                    metadata["name"] = metadata.get("name", Path(file_path).stem)
                    return metadata
            except Exception as e:
                # 忽略Front Matter解析错误，后面会尝试LLM解析
                logger.debug(f"解析 Front Matter 失败 (将尝试LLM): {e}")
                pass

            # 如果没有有效的Front Matter，使用LLM解析
            return self.parse_rule_content(content, file_path)

        except FileNotFoundError:
            logger.error(f"规则文件未找到: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取规则文件失败: {file_path}, 错误: {e}", exc_info=True)
            raise

    @abstractmethod
    def parse_rule_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """解析规则内容

        Args:
            content: 规则文本内容
            context: 上下文信息(如文件路径)

        Returns:
            Dict: 解析后的规则结构
        """
        raise NotImplementedError("子类必须实现 parse_rule_content 方法")

    def _get_default_result(self, file_path: str) -> Dict[str, Any]:
        """当解析失败时返回默认结果

        Args:
            file_path: 规则文件路径

        Returns:
            Dict: 默认的规则结构
        """
        return {
            "id": Path(file_path).stem,
            "name": Path(file_path).stem,
            "type": "manual",
            "description": "无法解析的规则文件",
            "globs": [],
            "always_apply": False,
            "items": [],
            "examples": [],
            "content": "",
        }

    def _is_valid_metadata(self, metadata: Dict[str, Any]) -> bool:
        """检查元数据是否有效

        Args:
            metadata: Front Matter元数据

        Returns:
            bool: 是否有效
        """
        # 至少应该包含name字段
        return bool(metadata.get("name")) or bool(metadata.get("id"))

    def _load_rule_content(self, file_path: str) -> str:
        """加载规则文件内容"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"规则文件未找到: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取规则文件失败: {file_path}, 错误: {e}")
            raise

    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析规则文件

        Args:
            file_path: 规则文件路径

        Returns:
            Dict[str, Any]: 解析后的规则结构
        """
        try:
            # 加载规则内容
            content = self._load_rule_content(file_path)
            # 解析规则内容
            parsed_rule = self.parse_rule_content(content, file_path)
            # 验证和增强
            validated_rule = self._validate_and_enhance(parsed_rule, file_path)
            return validated_rule
        except Exception as e:
            logger.error(f"解析规则文件失败: {file_path}, 错误: {e}", exc_info=True)
            # 返回包含错误的默认结果
            default_result = self._get_default_result(file_path)
            default_result["error"] = f"解析失败: {str(e)}"
            default_result["is_valid"] = False
            return default_result
