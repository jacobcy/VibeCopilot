"""
数据库命令基础模块

提供数据库命令处理器的基础类
"""

import logging
from typing import Any, Dict, Optional

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class BaseDatabaseCommand(BaseCommand, Command):
    """数据库命令基础处理器"""

    def __init__(self):
        """初始化基础处理器"""
        super().__init__(name="db", description="管理数据库")
        self._db_service = None

    def _init_services(self) -> None:
        """初始化数据库服务"""
        if not self.db_service:
            self._db_service = DatabaseService()

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """实现命令执行逻辑

        Args:
            args: 命令参数

        Returns:
            执行结果
        """
        result_code = self.handle(args)
        return {"success": result_code == 0, "code": result_code}

    @property
    def db_service(self) -> Optional[DatabaseService]:
        """获取数据库服务

        Returns:
            数据库服务实例
        """
        return self._db_service

    @db_service.setter
    def db_service(self, service: DatabaseService):
        """设置数据库服务

        Args:
            service: 数据库服务实例
        """
        self._db_service = service

    @classmethod
    def get_command(cls) -> str:
        """获取命令名称

        Returns:
            命令名称
        """
        return "db"

    @classmethod
    def get_description(cls) -> str:
        """获取命令描述

        Returns:
            命令描述
        """
        return "管理数据库，包括初始化、查询、创建、更新和删除操作"

    def handle(self, args: Dict) -> int:
        """处理命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        raise NotImplementedError("子类必须实现此方法")
