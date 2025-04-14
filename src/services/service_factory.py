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
            # 如果服务已经存在，直接返回缓存的实例
            if service_type in self._services and self._services[service_type] is not None:
                logger.debug(f"返回缓存的 {service_type} 服务实例 (ID: {id(self._services[service_type])})")
                return self._services[service_type]

            # 创建新的服务实例
            logger.debug(f"创建新的 {service_type} 服务实例")
            if service_type == "roadmap":
                from src.roadmap import RoadmapService

                self._services[service_type] = RoadmapService()
            elif service_type == "db":
                # 确保数据库表存在
                from src.db import ensure_tables_exist
                from src.db.service import DatabaseService

                ensure_tables_exist()  # 确保数据库表存在但不强制重建
                # 创建服务实例
                self._services[service_type] = DatabaseService()
            elif service_type == "task":
                # 确保数据库表存在
                from src.db import ensure_tables_exist
                from src.services.task import TaskService  # 使用新的模块化任务服务

                ensure_tables_exist()  # 确保数据库表存在但不强制重建
                # 创建服务实例
                self._services[service_type] = TaskService()
            elif service_type == "flow_session":
                from src.flow_session.manager import FlowSessionManager

                self._services[service_type] = FlowSessionManager(**kwargs)
            elif service_type == "status":
                from src.status.service import StatusService

                # 使用单例模式
                self._services[service_type] = StatusService.get_instance()
            else:
                raise ValueError(f"未知的服务类型: {service_type}")

            logger.debug(f"成功创建 {service_type} 服务实例 (ID: {id(self._services[service_type])})")
            return self._services[service_type]
        except Exception as e:
            logger.error(f"创建 {service_type} 服务实例失败: {e}")
            raise
