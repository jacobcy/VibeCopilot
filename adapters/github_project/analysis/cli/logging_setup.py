#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志设置模块.

提供日志配置功能，用于设置日志级别和格式。
"""

import logging


def setup_logging(verbose: bool = False):
    """设置日志.

    配置日志系统，根据verbose参数设置不同的日志级别。

    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 设置第三方库的日志级别为WARNING，减少无关日志输出
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if verbose:
        logging.debug("已启用详细日志模式")
    else:
        logging.info("已启用标准日志模式")
