"""
模板导出器模块

负责将数据库中的模板导出为文件格式
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.models import Template

logger = logging.getLogger(__name__)


def export_template_to_markdown(template: Union[Template, Dict[str, Any]], with_front_matter: bool = True) -> str:
    """
    将模板导出为Markdown格式

    Args:
        template: 模板对象或模板数据字典
        with_front_matter: 是否包含YAML前置元数据

    Returns:
        Markdown格式的模板内容
    """
    # 如果输入是字典，则直接使用
    if isinstance(template, dict):
        template_dict = template
    # 如果输入是Template对象，则转换为字典
    else:
        template_dict = template.dict() if hasattr(template, "dict") else template.model_dump()

    # 提取元数据
    metadata = template_dict.get("metadata", {})
    if not metadata and "author" in template_dict:
        # 如果元数据不在metadata字段，则尝试从顶层字段构建
        metadata = {
            "author": template_dict.get("author", "VibeCopilot"),
            "version": template_dict.get("version", "1.0.0"),
            "tags": template_dict.get("tags", []),
            "created_at": template_dict.get("created_at", datetime.now().isoformat()),
            "updated_at": template_dict.get("updated_at", datetime.now().isoformat()),
        }

    # 准备前置元数据
    front_matter = {
        "title": template_dict.get("name", template_dict.get("id", "")),
        "description": template_dict.get("description", ""),
        "type": template_dict.get("type", "general"),
        "author": metadata.get("author", "VibeCopilot"),
        "version": metadata.get("version", "1.0.0"),
        "tags": metadata.get("tags", []),
        "created_at": metadata.get("created_at", datetime.now().isoformat()),
        "updated_at": metadata.get("updated_at", datetime.now().isoformat()),
    }

    # 添加自定义元数据
    for key, value in metadata.items():
        if key not in front_matter:
            front_matter[key] = value

    # 获取模板内容
    content = template_dict.get("content", "")

    # 如果需要前置元数据，则添加
    if with_front_matter:
        # 将前置元数据转换为YAML
        front_matter_yaml = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)
        result = f"---\n{front_matter_yaml}---\n\n{content}"
    else:
        result = content

    return result


def export_template_to_file(template: Union[Template, Dict[str, Any]], output_path: str, format: str = "markdown") -> str:
    """
    将模板导出到文件

    Args:
        template: 模板对象或模板数据字典
        output_path: 输出文件路径
        format: 输出格式，支持markdown和json

    Returns:
        导出的文件路径
    """
    # 确保输出目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 根据格式导出
        if format.lower() == "json":
            # 如果是字典，则直接使用
            if isinstance(template, dict):
                template_dict = template
            # 如果是Template对象，则转换为字典
            else:
                template_dict = template.dict() if hasattr(template, "dict") else template.model_dump()

            # 写入JSON文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(template_dict, f, ensure_ascii=False, indent=2)
        else:
            # 默认导出为Markdown
            content = export_template_to_markdown(template)

            # 写入文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

        logger.info(f"模板已导出到: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"导出模板失败: {str(e)}")
        raise ValueError(f"导出模板失败: {str(e)}")


def batch_export_templates(templates: List[Union[Template, Dict[str, Any]]], output_dir: str, format: str = "markdown") -> List[str]:
    """
    批量导出模板

    Args:
        templates: 模板对象或模板数据字典列表
        output_dir: 输出目录
        format: 输出格式，支持markdown和json

    Returns:
        导出的文件路径列表
    """
    # 确保输出目录存在
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = []

    for template in templates:
        try:
            # 获取模板ID或名称作为文件名
            if isinstance(template, dict):
                template_id = template.get("id") or template.get("name", "template")
            else:
                template_id = template.id if hasattr(template, "id") else "template"

            # 确定文件扩展名
            extension = ".md" if format.lower() == "markdown" else ".json"

            # 构建输出文件路径
            output_path = output_dir / f"{template_id}{extension}"

            # 导出模板
            exported_file = export_template_to_file(template, str(output_path), format)
            exported_files.append(exported_file)

        except Exception as e:
            logger.error(f"导出模板 {template_id if 'template_id' in locals() else '未知'} 失败: {str(e)}")

    return exported_files
