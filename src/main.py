#!/usr/bin/env python3
"""
VibeCopilot - AI辅助项目管理工具

主入口文件
"""

import os
from typing import Optional

from src.core.log_init import get_logger, init_logging
from src.db import init_db

# 初始化日志系统
config_path = os.path.join("config", "logging.yaml")
init_logging(config_path)

# 获取主程序日志记录器
logger = get_logger(__name__)


def init_app() -> None:
    """初始化应用程序"""
    try:
        # 初始化数据库
        init_db()
        logger.info("数据库初始化成功")

        # 其他初始化操作...

    except Exception as e:
        logger.error(f"应用程序初始化失败: {str(e)}")
        raise


def main() -> None:
    """主程序入口"""
    try:
        # 初始化应用
        init_app()
        logger.info("VibeCopilot启动成功")

        # 主程序逻辑...

    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        raise


if __name__ == "__main__":
    main()
