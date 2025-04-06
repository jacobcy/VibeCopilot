"""
数据库命令基础模块

提供数据库命令的基础功能和服务初始化
"""

import logging
from typing import Any, Dict

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class BaseDatabaseCommand(BaseCommand, Command):
    """数据库命令基类"""

    def __init__(self):
        """初始化数据库命令"""
        super().__init__(name="db", description="管理数据库")
        self.db_service = None

    def _init_services(self) -> None:
        """初始化数据库服务"""
        if not self.db_service:
            self.db_service = DatabaseService()

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

    @classmethod
    def get_help(cls) -> str:
        """获取命令帮助信息

        Returns:
            命令帮助信息
        """
        return """
数据库管理命令

用法:
  vibecopilot db init                        - 初始化数据库
  vibecopilot db query --type=<类型>         - 查询实体列表或单个实体
  vibecopilot db create --type=<类型> --data='json字符串' - 创建实体
  vibecopilot db update --type=<类型> --id=<ID> --data='json字符串' - 更新实体
  vibecopilot db delete --type=<类型> --id=<ID> - 删除实体

参数:
  --type      实体类型(epic/story/task/label/template)
  --id        实体ID
  --data      JSON格式的数据
  --format    输出格式(text/json)，默认为text
  --query     查询字符串
  --tags      标签列表，逗号分隔
        """
