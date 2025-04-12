#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模板管理模块

提供创建、获取、更新和删除工作流模板的功能
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file
from src.workflow.operations import create_workflow

# 设置日志
logger = logging.getLogger(__name__)


def get_workflow_templates_directory() -> str:
    """
    获取工作流模板目录路径

    Returns:
        str: 工作流模板目录的完整路径
    """
    config = get_config()
    templates_dir = config.get("paths.templates_dir", "")
    return os.path.join(templates_dir, "workflow")


def list_workflow_templates() -> List[Dict[str, Any]]:
    """
    列出所有可用的工作流模板

    Returns:
        List[Dict[str, Any]]: 工作流模板列表
    """
    templates_dir = get_workflow_templates_directory()
    templates = []

    if not os.path.exists(templates_dir):
        logger.warning(f"工作流模板目录不存在: {templates_dir}")
        return templates

    for filename in os.listdir(templates_dir):
        if filename.endswith(".json"):
            try:
                template_path = os.path.join(templates_dir, filename)
                template = read_json_file(template_path)
                templates.append(template)
            except Exception as e:
                logger.error(f"读取模板文件出错 {filename}: {str(e)}")

    return templates


def load_templates_from_dir(directory_path: str) -> List[Dict[str, Any]]:
    """
    从指定目录加载所有模板文件

    Args:
        directory_path: 模板目录路径

    Returns:
        List[Dict[str, Any]]: 加载的模板列表
    """
    templates = []
    directory = Path(directory_path)

    if not directory.exists() or not directory.is_dir():
        logger.warning(f"模板目录不存在: {directory_path}")
        return templates

    for file_path in directory.glob("**/*.json"):
        try:
            template = parse_template_file(str(file_path))
            if template:
                templates.append(template)
        except Exception as e:
            logger.error(f"解析模板文件失败 {file_path}: {str(e)}")

    return templates


def parse_template_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    解析模板文件

    Args:
        file_path: 模板文件路径

    Returns:
        Optional[Dict[str, Any]]: 解析后的模板数据，如果解析失败则返回None
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"模板文件不存在: {file_path}")
            return None

        template_data = read_json_file(file_path)

        # 确保模板有ID
        if "id" not in template_data:
            template_id = str(uuid.uuid4())
            template_data["id"] = template_id

            # 保存更新后的模板
            write_json_file(file_path, template_data)

        return template_data
    except Exception as e:
        logger.error(f"解析模板文件失败 {file_path}: {str(e)}")
        return None


def get_workflow_template(template_id: str) -> Optional[Dict[str, Any]]:
    """
    获取指定ID的工作流模板

    Args:
        template_id (str): 模板ID

    Returns:
        Optional[Dict[str, Any]]: 如果找到则返回模板数据，否则返回None
    """
    templates = list_workflow_templates()

    for template in templates:
        if template.get("id") == template_id:
            return template

    return None


def create_workflow_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建新的工作流模板

    Args:
        template_data (Dict[str, Any]): 模板数据

    Returns:
        Dict[str, Any]: 创建的模板数据，包含生成的ID
    """
    templates_dir = get_workflow_templates_directory()
    ensure_directory_exists(templates_dir)

    # 生成唯一ID
    template_id = str(uuid.uuid4())
    template_data["id"] = template_id

    # 写入模板文件
    template_path = os.path.join(templates_dir, f"{template_id}.json")
    write_json_file(template_path, template_data)

    logger.info(f"创建工作流模板成功: {template_id}")
    return template_data


def update_workflow_template(template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新现有的工作流模板

    Args:
        template_id (str): 要更新的模板ID
        template_data (Dict[str, Any]): 新的模板数据

    Returns:
        Dict[str, Any]: 操作结果
    """
    templates_dir = get_workflow_templates_directory()
    template_path = os.path.join(templates_dir, f"{template_id}.json")

    if not os.path.exists(template_path):
        logger.warning(f"要更新的模板不存在: {template_id}")
        return {"success": False, "error": "Template not found", "template_id": template_id}

    # 确保ID一致
    template_data["id"] = template_id

    # 写入更新后的模板
    write_json_file(template_path, template_data)

    logger.info(f"更新工作流模板成功: {template_id}")
    return {"success": True, "template_id": template_id}


def delete_workflow_template(template_id: str) -> Dict[str, Any]:
    """
    删除工作流模板

    Args:
        template_id (str): 要删除的模板ID

    Returns:
        Dict[str, Any]: 操作结果
    """
    templates_dir = get_workflow_templates_directory()
    template_path = os.path.join(templates_dir, f"{template_id}.json")

    if not os.path.exists(template_path):
        logger.warning(f"要删除的模板不存在: {template_id}")
        return {"success": False, "error": "Template not found", "template_id": template_id}

    # 删除模板文件
    os.remove(template_path)

    logger.info(f"删除工作流模板成功: {template_id}")
    return {"success": True, "template_id": template_id}


def create_workflow_from_template(template_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    基于模板创建新的工作流

    Args:
        template_id (str): 模板ID
        workflow_data (Dict[str, Any]): 工作流数据，将覆盖模板中的同名字段

    Returns:
        Optional[Dict[str, Any]]: 创建的工作流数据，如果模板不存在则返回None
    """
    template = get_workflow_template(template_id)

    if not template:
        logger.warning(f"创建工作流失败: 模板不存在 {template_id}")
        return None

    # 合并模板数据和工作流数据
    merged_data = {"steps": template.get("steps", []), "template_id": template_id}

    # 工作流数据会覆盖模板中的同名字段
    merged_data.update(workflow_data)

    # 创建工作流
    workflow = create_workflow(merged_data)
    logger.info(f"基于模板 {template_id} 创建工作流成功: {workflow.get('id')}")

    return workflow
