#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流服务模块

提供统一的工作流服务接口，集成会话管理和工作流操作功能。
使用组件化设计，将不同职责委托给专门的服务组件。
"""

import logging
from typing import Any, Dict, List, Optional

from src.db import get_session_factory
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager
from src.workflow.service.components import BaseService, ExecutionService, SessionService, StageService, WorkflowDefinitionService
from src.workflow.workflow_operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_name,
    get_workflow_by_type,
    list_workflows,
    update_workflow,
    validate_workflow_files,
)

logger = logging.getLogger(__name__)


class FlowService(BaseService):
    """
    工作流服务类，整合工作流和会话管理功能

    采用组件化设计，将职责分散到各个专门的服务组件中
    """

    def __init__(self, verbose=False):
        """初始化工作流服务

        Args:
            verbose: 是否显示详细日志
        """
        # 调用基类初始化
        super().__init__(verbose)

        # 初始化组件服务
        self.workflow_service = WorkflowDefinitionService(verbose)
        self.session_service = SessionService(self.session_manager, verbose)
        self.stage_service = StageService(self.stage_manager, verbose)
        self.execution_service = ExecutionService(self.session_manager, verbose)

    # ============= 工作流定义相关方法 =============

    def list_workflows(self, workflow_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取工作流列表

        Args:
            workflow_type: 可选的工作流类型过滤

        Returns:
            包含工作流列表的字典
        """
        return self.workflow_service.list_workflows(workflow_type)

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义字典或None
        """
        return self.workflow_service.get_workflow(workflow_id)

    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流定义（get_workflow的别名）

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义字典或None
        """
        return self.get_workflow(workflow_id)

    def get_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        按名称获取工作流定义

        Args:
            name: 工作流名称

        Returns:
            工作流定义字典或None
        """
        return self.workflow_service.get_workflow_by_name(name)

    def get_workflow_by_type(self, workflow_type: str) -> List[Dict[str, Any]]:
        """
        按类型获取工作流定义

        Args:
            workflow_type: 工作流类型

        Returns:
            工作流定义列表
        """
        return self.workflow_service.get_workflow_by_type(workflow_type)

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流定义

        Args:
            workflow_data: 工作流数据

        Returns:
            创建的工作流定义
        """
        return self.workflow_service.create_workflow(workflow_data)

    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新工作流定义

        Args:
            workflow_id: 工作流ID
            workflow_data: 更新的工作流数据

        Returns:
            更新后的工作流定义或None
        """
        return self.workflow_service.update_workflow(workflow_id, workflow_data)

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            是否删除成功
        """
        return self.workflow_service.delete_workflow(workflow_id)

    def validate_workflows(self, auto_fix: bool = False) -> Dict[str, Any]:
        """
        验证工作流文件一致性

        Args:
            auto_fix: 是否自动修复问题

        Returns:
            验证结果
        """
        return validate_workflow_files(auto_fix=auto_fix)

    # ============= 会话管理相关方法 =============

    def create_session(self, workflow_id: str, name: Optional[str] = None, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        创建工作流会话

        Args:
            workflow_id: 工作流定义ID
            name: 会话名称(可选)
            task_id: 关联的任务ID(可选)，表明会话的目的是完成该任务

        Returns:
            创建的会话数据
        """
        return self.session_service.create_session(workflow_id, name, task_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话详情

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典或None
        """
        return self.session_service.get_session(session_id)

    def list_sessions(self, status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出会话

        Args:
            status: 会话状态过滤
            workflow_id: 工作流ID过滤

        Returns:
            会话数据列表
        """
        return self.session_service.list_sessions(status, workflow_id)

    def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新会话数据

        Args:
            session_id: 会话ID
            data: 更新数据

        Returns:
            更新后的会话数据或None
        """
        return self.session_service.update_session(session_id, data)

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        return self.session_service.delete_session(session_id)

    def pause_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        暂停会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        return self.session_service.pause_session(session_id)

    def resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        恢复会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        return self.session_service.resume_session(session_id)

    def complete_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        完成会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        return self.session_service.complete_session(session_id)

    def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """结束工作流会话

        将会话状态设置为CLOSED，表示会话已结束。

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话数据或None
        """
        return self.session_service.close_session(session_id)

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        获取当前活跃会话

        Returns:
            当前会话数据字典或None
        """
        return self.session_service.get_current_session()

    # ============= 阶段管理相关方法 =============

    def get_stage_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        获取阶段实例

        Args:
            instance_id: 实例ID

        Returns:
            阶段实例数据或None
        """
        return self.stage_service.get_stage_instance(instance_id)

    def get_session_stages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的所有阶段实例

        Args:
            session_id: 会话ID

        Returns:
            阶段实例数据列表
        """
        return self.stage_service.get_session_stages(session_id)

    def complete_stage(self, instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        完成阶段

        Args:
            instance_id: 阶段实例ID
            context: 上下文数据(可选)

        Returns:
            更新后的阶段实例数据或None
        """
        return self.stage_service.complete_stage(instance_id, context)

    def create_stage_instance(self, session_id: str, stage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建阶段实例

        Args:
            session_id: 会话ID
            stage_data: 阶段数据

        Returns:
            创建的阶段实例数据或None
        """
        return self.stage_service.create_stage_instance(session_id, stage_data)

    # ============= 工作流执行相关方法 =============

    def execute_workflow(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None, task_id: Optional[str] = None, session_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行工作流

        此方法是关键的连接点，将workflow和flow_session模块连接起来。
        不在workflow模块中实现执行逻辑，而是委托给flow_session模块。

        Args:
            workflow_id: 工作流ID
            context: 可选的执行上下文数据
            task_id: 可选的特定任务ID
            session_name: 可选的会话名称

        Returns:
            执行结果字典
        """
        return self.execution_service.execute_workflow(workflow_id, context, task_id, session_name)
