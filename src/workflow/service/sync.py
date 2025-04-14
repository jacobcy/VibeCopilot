#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流同步操作

提供工作流与数据库的同步功能。
"""

import datetime
import logging
from typing import Any, Dict

from src.db import get_session_factory, init_db
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db.workflow_definition import WorkflowDefinition

logger = logging.getLogger(__name__)


def sync_workflow_to_db(workflow_data: Dict[str, Any], verbose: bool = False) -> bool:
    """
    将工作流定义同步到数据库

    Args:
        workflow_data: 工作流定义数据
        verbose: 是否显示详细日志

    Returns:
        bool: 同步是否成功
    """
    if not workflow_data:
        if verbose:
            logger.error("同步工作流到数据库失败: 工作流数据为空")
        return False

    workflow_id = workflow_data.get("id")
    if not workflow_id:
        if verbose:
            logger.error("同步工作流到数据库失败: 工作流ID为空")
        return False

    try:
        # 初始化数据库
        init_db()
        session_factory = get_session_factory()

        with session_factory() as session:
            # 检查工作流是否已存在
            repo = WorkflowDefinitionRepository(session)
            existing = repo.get_by_id(workflow_id)

            if existing:
                if verbose:
                    logger.info(f"工作流已存在于数据库中: {workflow_id}, 更新现有记录")

                # 提取需要的字段
                stages = workflow_data.get("stages", [])
                source_rule = workflow_data.get("source_rule")

                # 更新工作流定义
                existing.name = workflow_data.get("name", existing.name)
                existing.type = workflow_data.get("type", existing.type)
                existing.description = workflow_data.get("description", existing.description)
                existing.stages = stages
                existing.source_rule = source_rule
                existing.updated_at = datetime.datetime.utcnow()

                session.commit()
                if verbose:
                    logger.info(f"更新工作流定义成功: {workflow_id}")
                return True
            else:
                if verbose:
                    logger.info(f"工作流不存在于数据库中: {workflow_id}, 创建新记录")

                # 提取需要的字段
                name = workflow_data.get("name", "未命名工作流")
                workflow_type = workflow_data.get("type")
                description = workflow_data.get("description", "")
                stages = workflow_data.get("stages", [])
                source_rule = workflow_data.get("source_rule")

                # 创建工作流定义
                new_definition = WorkflowDefinition(
                    id=workflow_id, name=name, type=workflow_type, description=description, stages=stages, source_rule=source_rule
                )

                session.add(new_definition)
                session.commit()
                if verbose:
                    logger.info(f"创建工作流定义成功: {workflow_id}")
                return True
    except Exception as e:
        if verbose:
            logger.exception(f"同步工作流到数据库失败: {str(e)}")
        return False
