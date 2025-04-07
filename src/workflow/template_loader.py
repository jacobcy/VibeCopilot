#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模板加载器

提供从模板文件加载工作流定义的功能
"""

import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from src.workflow.config import get_template_path, list_templates

logger = logging.getLogger(__name__)


def load_flow_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    加载工作流模板

    Args:
        template_name: 模板名称

    Returns:
        模板数据字典，如果加载失败返回None
    """
    try:
        template_path = get_template_path(template_name)
        if not os.path.exists(template_path):
            logger.error(f"模板文件不存在: {template_path}")
            return None

        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)

        logger.info(f"成功加载模板: {template_name}")
        return template_data
    except Exception as e:
        logger.exception(f"加载模板 {template_name} 时出错")
        return None


def create_workflow_from_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    从模板创建工作流

    Args:
        template_name: 模板名称

    Returns:
        工作流数据字典，如果创建失败返回None
    """
    template_data = load_flow_template(template_name)
    if not template_data:
        return None

    try:
        # 生成新工作流ID
        workflow_id = str(uuid.uuid4())

        # 创建工作流数据
        workflow_data = {
            "id": workflow_id,
            "name": template_data.get("name", f"基于{template_name}的工作流"),
            "description": template_data.get("description", "从模板创建的工作流"),
            "source_template": template_name,
            "version": template_data.get("version", "1.0.0"),
            "stages": template_data.get("stages", []),
            "transitions": template_data.get("transitions", []),
            "status": "active",
        }

        logger.info(f"从模板 {template_name} 创建工作流: {workflow_id}")
        return workflow_data
    except Exception as e:
        logger.exception(f"从模板 {template_name} 创建工作流时出错")
        return None


def get_available_templates() -> List[Dict[str, Any]]:
    """
    获取所有可用的工作流模板信息

    Returns:
        模板信息列表
    """
    template_names = list_templates()
    templates = []

    for name in template_names:
        template = load_flow_template(name)
        if template:
            templates.append(
                {
                    "id": name,
                    "name": template.get("name", name),
                    "description": template.get("description", ""),
                    "version": template.get("version", "1.0.0"),
                }
            )

    return templates
