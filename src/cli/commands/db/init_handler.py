"""
数据库初始化处理模块

处理数据库初始化相关命令
"""

import logging
from typing import Any, Dict

from .base import BaseDatabaseCommand, logger


class InitHandler:
    """数据库初始化处理器"""

    @staticmethod
    def handle(command: BaseDatabaseCommand, args: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化操作

        Args:
            command: 数据库命令实例
            args: 命令参数

        Returns:
            执行结果
        """
        logger.info("初始化数据库")

        try:
            # 数据库已通过服务初始化
            command._init_services()

            # 仅初始化
            return {
                "success": True,
                "message": "已初始化数据库",
            }
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            return {"success": False, "error": f"初始化数据库失败: {e}"}
