"""
规则解析器模块

提供对规则文件和内容的解析功能，使用parsing模块进行实际解析
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config import ConfigManager
from src.models.rule_model import Example, Rule, RuleItem, RuleMetadata
from src.parsing import parser_factory
from src.parsing.base_parser import BaseParser
from src.parsing.parsers.openai_parser import OpenAIParser

logger = logging.getLogger(__name__)


def parse_rule_file(file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """解析规则文件

    使用parsing模块解析规则文件为结构化数据

    Args:
        file_path: 规则文件路径
        parser_type: 解析器类型，如不指定则根据文件类型自动选择
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构，符合Rule模型格式
    """
    logger.info(f"使用parsing模块解析规则文件: {file_path}")

    # 创建配置
    config_manager = ConfigManager()
    parser_config = config_manager.config.get("parsing", {})
    if model:
        parser_config["model"] = model

    # 获取合适的解析器
    parser = None
    if parser_type:
        if parser_type.lower() == "openai":
            parser = OpenAIParser(config=parser_config)
        # 可以添加其他类型的解析器
    else:
        # 使用解析器工厂自动选择解析器
        parser = parser_factory.get_parser_for_file(file_path, config=parser_config)

    if not parser:
        # 默认使用OpenAI解析器
        logger.info(f"未指定解析器，使用默认OpenAI解析器")
        parser = OpenAIParser(config=parser_config)

    # 使用解析器解析文件
    parsed_data = parser.parse_file(file_path, content_type="rule")

    # 确保解析结果包含必要字段
    path = Path(file_path)
    if not parsed_data:
        logger.warning(f"解析器未返回有效数据，使用简单解析")
        parsed_data = {
            "id": path.stem,
            "name": path.stem,
            "type": "rule",
            "description": f"从文件 {path.name} 导入的规则",
            "content": path.read_text(encoding="utf-8"),
        }

    # 确保有必要的字段
    if "id" not in parsed_data:
        parsed_data["id"] = path.stem

    if "name" not in parsed_data:
        parsed_data["name"] = path.stem

    if "type" not in parsed_data:
        parsed_data["type"] = "rule"

    if "content" not in parsed_data and path.exists():
        # 如果没有content字段，使用文件内容
        parsed_data["content"] = path.read_text(encoding="utf-8")

    # 确保规则数据符合标准结构
    rule_data = ensure_rule_structure(parsed_data, path.name)

    logger.info(f"规则文件解析完成: {file_path}")
    return rule_data


def parse_rule_content(content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """解析规则内容

    使用parsing模块解析规则内容为结构化数据

    Args:
        content: 规则文本内容
        context: 上下文信息(文件路径等)
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构，符合Rule模型格式
    """
    logger.info(f"使用parsing模块解析规则内容, 上下文: {context}")

    # 创建配置
    config_manager = ConfigManager()
    parser_config = config_manager.config.get("parsing", {})
    if model:
        parser_config["model"] = model

    # 选择解析器
    parser = None
    if parser_type:
        if parser_type.lower() == "openai":
            parser = OpenAIParser(config=parser_config)
        # 可以添加其他类型的解析器
    else:
        # 默认使用OpenAI解析器
        logger.info(f"未指定解析器类型，使用默认OpenAI解析器")
        parser = OpenAIParser(config=parser_config)

    # 使用解析器解析内容
    parsed_data = parser.parse_text(content, content_type="rule")

    # 确保解析结果包含必要字段
    if not parsed_data:
        logger.warning(f"解析器未返回有效数据，使用简单解析")
        parsed_data = {
            "id": f"rule_{hashlib.md5(content.encode()).hexdigest()[:8]}",
            "name": "未命名规则",
            "type": "rule",
            "description": "从内容导入的规则",
            "content": content,
        }

    # 确保有必要的字段
    if "id" not in parsed_data and context:
        # 如果有上下文（例如文件名），使用它作为ID
        path = Path(context)
        parsed_data["id"] = path.stem
    elif "id" not in parsed_data:
        # 否则生成一个基于内容的ID
        hash_obj = hashlib.md5(content.encode())
        parsed_data["id"] = f"rule_{hash_obj.hexdigest()[:8]}"

    if "name" not in parsed_data:
        if context:
            path = Path(context)
            parsed_data["name"] = path.stem
        else:
            parsed_data["name"] = "未命名规则"

    if "type" not in parsed_data:
        parsed_data["type"] = "rule"

    if "content" not in parsed_data:
        parsed_data["content"] = content

    # 确保规则数据符合标准结构
    rule_data = ensure_rule_structure(parsed_data, context or "内容解析")

    logger.info(f"规则内容解析完成")
    return rule_data


def ensure_rule_structure(parsed_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """确保规则数据符合标准结构

    处理解析结果，确保其符合Rule模型的格式要求

    Args:
        parsed_data: 解析得到的原始数据
        source: 数据来源，用于生成默认值

    Returns:
        Dict: 符合Rule模型要求的数据结构
    """
    # 基本属性
    rule_data = {
        "id": parsed_data.get("id", f"rule_{hashlib.md5(source.encode()).hexdigest()[:8]}"),
        "name": parsed_data.get("name", "未命名规则"),
        "type": parsed_data.get("type", "rule"),
        "description": parsed_data.get("description", f"从{source}导入的规则"),
        "content": parsed_data.get("content", ""),
        "globs": parsed_data.get("globs", []),
        "always_apply": parsed_data.get("always_apply", False),
    }

    # 处理规则条目
    items = []
    if "items" in parsed_data and isinstance(parsed_data["items"], list):
        for item in parsed_data["items"]:
            if isinstance(item, dict):
                items.append({"content": item.get("content", ""), "priority": item.get("priority", 0), "category": item.get("category", None)})
            elif isinstance(item, str):
                items.append({"content": item, "priority": 0, "category": None})
    rule_data["items"] = items

    # 处理规则示例
    examples = []
    if "examples" in parsed_data and isinstance(parsed_data["examples"], list):
        for example in parsed_data["examples"]:
            if isinstance(example, dict):
                examples.append(
                    {
                        "content": example.get("content", ""),
                        "is_valid": example.get("is_valid", True),
                        "description": example.get("description", None),
                    }
                )
            elif isinstance(example, str):
                examples.append({"content": example, "is_valid": True, "description": None})
    rule_data["examples"] = examples

    # 处理元数据
    metadata = parsed_data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    # 确保元数据符合RuleMetadata模型
    rule_data["metadata"] = {
        "author": metadata.get("author", "VibeCopilot"),
        "tags": metadata.get("tags", []),
        "version": metadata.get("version", "1.0.0"),
        "created_at": metadata.get("created_at", datetime.now().isoformat()),
        "updated_at": metadata.get("updated_at", datetime.now().isoformat()),
        "dependencies": metadata.get("dependencies", []),
        "usage_count": metadata.get("usage_count", 0),
        "effectiveness": metadata.get("effectiveness", 0),
    }

    return rule_data
