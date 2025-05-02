"""
模板初始化数据模块

提供模板表的初始数据
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict

from src.core.config import refresh_config
from src.db import get_session
from src.db.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


def init_templates() -> Dict[str, int]:
    """初始化模板数据，并返回统计"""
    # 刷新配置
    refresh_config()

    session = get_session()
    # Initialize repo without session
    repo = TemplateRepository()

    success_count = 0
    fail_count = 0

    # 检查模板表是否为空
    if repo.count(session) == 0:
        logger.info("模板表为空，开始初始化默认模板...")
        # 添加一些示例模板
        templates = [
            {
                "id": f"tpl_{uuid.uuid4().hex[:8]}",
                "name": "需求文档模板",
                "description": "用于创建需求文档的标准模板",
                "type": "prd",
                "content": """
# {{ title }}

## 1. 背景

## 2. 目标

## 3. 需求详述

## 4. 验收标准

""",
                "author": "system",
                "version": "1.0.0",
                "tags": json.dumps(["document", "requirement", "prd"]),
            },
            {
                "id": f"tpl_{uuid.uuid4().hex[:8]}",
                "name": "任务描述模板",
                "description": "用于创建开发任务的标准模板",
                "type": "task",
                "content": """
**任务目标:** {{ objective }}
**实现细节:**

**验收标准:**

""",
                "author": "system",
                "version": "1.0.0",
                "tags": json.dumps(["task", "development"]),
            },
        ]

        for template in templates:
            try:
                # Pass session to create method
                repo.create(session, data=template)
                success_count += 1
            except Exception as e:
                logger.error(f"创建模板失败: {template['name']}", exc_info=True)
                fail_count += 1
    else:
        logger.info("模板表不为空，跳过初始化")

    logger.info(f"模板初始化完成: 成功 {success_count}, 失败 {fail_count}")
    session.close()
    return {"success": success_count, "failed": fail_count}
