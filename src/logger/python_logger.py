#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python日志工具

提供配置和获取Python标准日志记录器的功能，用于应用程序内部日志记录。
"""

import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

# 日志文件目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "app")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name, level=logging.INFO):
    """
    获取指定名称的日志记录器

    Args:
        name (str): 日志记录器名称
        level (int): 日志级别，默认为INFO

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 防止重复添加处理器
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)

        # 文件处理器 - 使用当前日期作为文件名
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(LOG_DIR, f"{name}_{today}.log")
        file_handler = RotatingFileHandler(file_path, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10MB
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)

    return logger


# 应用默认日志记录器
app_logger = get_logger("vibe_app")

# 导出工具函数和默认日志记录器
__all__ = ["get_logger", "app_logger"]
