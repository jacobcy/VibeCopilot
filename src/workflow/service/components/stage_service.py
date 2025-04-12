#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流阶段服务组件

提供工作流阶段实例的管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StageService:
    """工作流阶段服务类，负责阶段实例的管理"""

    def __init__(self, stage_manager, verbose=False):
        """初始化阶段服务

        Args:
            stage_manager: 阶段管理器实例
            verbose: 是否显示详细日志
        """
        self.stage_manager = stage_manager
        self.verbose = verbose

    def get_stage_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        获取阶段实例

        Args:
            instance_id: 实例ID

        Returns:
            阶段实例数据或None
        """
        if self.verbose:
            logger.debug(f"获取阶段实例: {instance_id}")

        instance = self.stage_manager.get_instance(instance_id)
        return instance.to_dict() if instance and hasattr(instance, "to_dict") else None

    def get_session_stages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话的所有阶段实例

        Args:
            session_id: 会话ID

        Returns:
            阶段实例数据列表
        """
        if self.verbose:
            logger.debug(f"获取会话的所有阶段: {session_id}")

        instances = self.stage_manager.get_session_instances(session_id)
        return [i.to_dict() if hasattr(i, "to_dict") else {"id": i.id} for i in instances]

    def complete_stage(self, instance_id: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        完成阶段

        Args:
            instance_id: 阶段实例ID
            context: 上下文数据(可选)

        Returns:
            更新后的阶段实例数据或None
        """
        if self.verbose:
            logger.info(f"完成阶段: {instance_id}")

        instance = self.stage_manager.complete_stage(instance_id, context)
        return instance.to_dict() if instance and hasattr(instance, "to_dict") else None

    def create_stage_instance(self, session_id: str, stage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建阶段实例

        Args:
            session_id: 会话ID
            stage_data: 阶段数据

        Returns:
            创建的阶段实例数据或None
        """
        if self.verbose:
            logger.info(f"创建阶段实例: {session_id}")

        instance = self.stage_manager.create_instance(session_id, stage_data)
        return instance.to_dict() if instance and hasattr(instance, "to_dict") else None
