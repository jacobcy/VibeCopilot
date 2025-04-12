"""
日志工具模块

提供统一的日志配置和管理功能。
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level: int = logging.INFO, log_file: Optional[str] = None, format_str: Optional[str] = None) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_str: 日志格式字符串（可选）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger

    # 设置默认格式
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(format_str)

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取一个已配置的日志记录器，如果不存在则创建新的

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    logger = logging.getLogger(name)

    # 如果日志记录器未配置，使用默认配置
    if not logger.handlers:
        # 设置默认日志文件
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # 使用日期作为日志文件名
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{date_str}.log")

        # 设置日志记录器
        logger = setup_logger(name=name, level=logging.INFO, log_file=log_file)

    return logger
