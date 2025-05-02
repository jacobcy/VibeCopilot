#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务工厂模块
"""
from typing import Any


class ServiceFactory:
    """服务工厂类"""

    def __init__(self):
        """初始化服务工厂"""
        self._services = {}

    def create_service(self, service_type: str = "roadmap", **kwargs) -> Any:
        """
        创建服务实例

        Args:
            service_type: 服务类型，默认为roadmap
            **kwargs: 额外的参数传递给服务实例

        Returns:
            服务实例
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # If service exists, return cached instance
            if service_type in self._services and self._services[service_type] is not None:
                logger.debug(f"返回缓存的 {service_type} 服务实例 (ID: {id(self._services[service_type])})")
                return self._services[service_type]

            # Create new service instance
            logger.debug(f"创建新的 {service_type} 服务实例")
            if service_type == "roadmap":
                from src.roadmap import RoadmapService

                # 过滤掉verbose参数，只传递config参数(如果存在)
                service_kwargs = {}
                if "config" in kwargs:
                    service_kwargs["config"] = kwargs["config"]

                self._services[service_type] = RoadmapService(**service_kwargs)
            elif service_type == "task":
                from src.db import ensure_tables_exist
                from src.services.task import TaskService

                ensure_tables_exist()
                self._services[service_type] = TaskService()
            elif service_type == "flow_session":
                from src.flow_session.manager import FlowSessionManager

                self._services[service_type] = FlowSessionManager(**kwargs)
            elif service_type == "status":
                from src.status.service import StatusService

                self._services[service_type] = StatusService.get_instance()
            elif service_type == "memory_item":
                from src.memory.services.memory_item_service import MemoryItemService

                self._services[service_type] = MemoryItemService(**kwargs)
            elif service_type == "note":
                from src.memory.services.note_service import NoteService

                self._services[service_type] = NoteService(**kwargs)
            elif service_type == "db":
                from src.db import DatabaseService

                self._services[service_type] = DatabaseService(**kwargs)
            else:
                raise ValueError(f"未知的服务类型: {service_type}")

            logger.debug(f"成功创建 {service_type} 服务实例 (ID: {id(self._services[service_type])})")
            return self._services[service_type]
        except Exception as e:
            logger.error(f"创建 {service_type} 服务实例失败: {e}")
            raise
