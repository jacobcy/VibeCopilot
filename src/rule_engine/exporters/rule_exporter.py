"""
规则导出器模块

提供规则导出为各种格式的功能
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from src.models.rule_model import Rule

logger = logging.getLogger(__name__)


def export_rule_to_yaml(rule_data: Union[Dict[str, Any], Rule], output_path: Optional[str] = None) -> str:
    """将规则数据导出为YAML格式

    Args:
        rule_data: 规则数据，可以是Rule对象或符合Rule结构的字典
        output_path: 输出文件路径，如不指定则返回YAML文本

    Returns:
        str: 如果没有指定输出路径，返回YAML文本；否则返回输出文件路径
    """
    # 如果传入的是Rule对象，转换为字典
    if isinstance(rule_data, Rule):
        rule_dict = rule_data.dict()
    else:
        rule_dict = rule_data

    rule_id = rule_dict.get("id", "unknown")
    logger.info(f"导出规则为YAML格式: {rule_id}")

    # 优化规则数据，只保留必要字段
    export_data = {
        "id": rule_dict.get("id"),
        "name": rule_dict.get("name"),
        "type": rule_dict.get("type", "rule"),
        "description": rule_dict.get("description", ""),
        "content": rule_dict.get("content", ""),
    }

    # 添加可选字段
    if "globs" in rule_dict and rule_dict["globs"]:
        export_data["globs"] = rule_dict["globs"]

    if "always_apply" in rule_dict and rule_dict["always_apply"]:
        export_data["always_apply"] = rule_dict["always_apply"]

    # 添加条目
    if "items" in rule_dict and rule_dict["items"]:
        export_data["items"] = []
        for item in rule_dict["items"]:
            if isinstance(item, dict):
                export_data["items"].append(item)
            else:
                # 如果是Pydantic模型，转换为字典
                try:
                    export_data["items"].append(item.dict())
                except AttributeError:
                    # 如果不是Pydantic模型且不是字典，跳过
                    logger.warning(f"跳过无法处理的规则条目: {item}")

    # 添加示例
    if "examples" in rule_dict and rule_dict["examples"]:
        export_data["examples"] = []
        for example in rule_dict["examples"]:
            if isinstance(example, dict):
                export_data["examples"].append(example)
            else:
                # 如果是Pydantic模型，转换为字典
                try:
                    export_data["examples"].append(example.dict())
                except AttributeError:
                    # 如果不是Pydantic模型且不是字典，跳过
                    logger.warning(f"跳过无法处理的规则示例: {example}")

    # 添加元数据
    if "metadata" in rule_dict:
        metadata = rule_dict["metadata"]
        if isinstance(metadata, dict):
            export_data["metadata"] = metadata
        else:
            # 如果是Pydantic模型，转换为字典
            try:
                export_data["metadata"] = metadata.dict()
            except AttributeError:
                # 如果不是Pydantic模型且不是字典，创建空元数据
                logger.warning(f"无法处理的元数据格式: {metadata}")
                export_data["metadata"] = {}
    elif "front_matter" in rule_dict:
        # 如果有front_matter，将其转换为metadata
        export_data["metadata"] = {k: v for k, v in rule_dict["front_matter"].items() if k not in ["id", "name", "type", "description"]}

    # 转换为YAML
    yaml_text = yaml.dump(export_data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # 如果指定了输出路径，写入文件
    if output_path:
        output_path = Path(output_path)
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # 写入文件
        output_path.write_text(yaml_text, encoding="utf-8")
        logger.info(f"规则已导出到文件: {output_path}")
        return str(output_path)

    # 返回YAML文本
    return yaml_text
