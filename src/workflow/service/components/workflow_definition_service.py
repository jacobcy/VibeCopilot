#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流定义服务组件

提供工作流定义的管理功能，是workflow模块的服务接口。
"""

import logging
from typing import Any, Dict, List, Optional

from src.workflow.operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_name,
    get_workflow_by_type,
    list_workflows,
    update_workflow,
)

logger = logging.getLogger(__name__)


class WorkflowDefinitionService:
    """工作流定义服务类，负责工作流定义的CRUD操作"""

    def __init__(self, verbose=False):
        """初始化工作流定义服务

        Args:
            verbose: 是否显示详细日志
        """
        self.verbose = verbose

    def list_workflows(self, workflow_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取工作流列表

        Args:
            workflow_type: 可选的工作流类型过滤

        Returns:
            包含工作流列表的字典
        """
        if self.verbose:
            logger.debug(f"列出工作流列表 (类型过滤: {workflow_type})")

        workflows = list_workflows()

        if workflow_type:
            # 如果指定了类型，进行过滤
            if isinstance(workflows, list):
                workflows = [wf for wf in workflows if wf.get("type") == workflow_type]
            elif isinstance(workflows, dict) and "workflows" in workflows:
                workflows["workflows"] = [wf for wf in workflows["workflows"] if wf.get("type") == workflow_type]

        # 确保返回一致的数据结构
        if isinstance(workflows, list):
            return {"workflows": workflows}
        return workflows

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义字典或None
        """
        if self.verbose:
            logger.debug(f"获取工作流定义: {workflow_id}")

        return get_workflow(workflow_id, self.verbose)

    def get_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        按名称获取工作流定义

        Args:
            name: 工作流名称

        Returns:
            工作流定义字典或None
        """
        if self.verbose:
            logger.debug(f"按名称获取工作流: {name}")

        return get_workflow_by_name(name)

    def get_workflow_by_type(self, workflow_type: str) -> List[Dict[str, Any]]:
        """
        按类型获取工作流定义

        Args:
            workflow_type: 工作流类型

        Returns:
            工作流定义列表
        """
        if self.verbose:
            logger.debug(f"按类型获取工作流: {workflow_type}")

        return get_workflow_by_type(workflow_type)

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流定义

        Args:
            workflow_data: 工作流数据

        Returns:
            创建的工作流定义
        """
        if self.verbose:
            logger.info(f"创建工作流: {workflow_data.get('name', '未命名工作流')}")

        return create_workflow(workflow_data)

    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新工作流定义

        Args:
            workflow_id: 工作流ID
            workflow_data: 更新的工作流数据

        Returns:
            更新后的工作流定义或None
        """
        if self.verbose:
            logger.info(f"更新工作流: {workflow_id}")

        return update_workflow(workflow_id, workflow_data)

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            是否删除成功
        """
        if self.verbose:
            logger.info(f"删除工作流: {workflow_id}")

        return delete_workflow(workflow_id)
