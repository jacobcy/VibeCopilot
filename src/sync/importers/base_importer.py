"""
基础导入器模块

提供所有导入器的基类。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.utils.console_utils import print_error, print_success

logger = logging.getLogger(__name__)


class BaseImporter:
    """所有导入器的基类"""

    def __init__(self, service, verbose: bool = False, stop_on_error: bool = True):
        """
        初始化基础导入器

        Args:
            service: 路线图服务
            verbose: 是否启用详细日志
            stop_on_error: 是否在遇到错误时停止
        """
        self.service = service
        self.verbose = verbose
        self.stop_on_error = stop_on_error

    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(message)
        if self.verbose:
            logger.debug(message)

    def log_success(self, message: str):
        """记录成功日志"""
        logger.info(message)
        print_success(message)

    def log_error(self, message: str, error: Optional[Exception] = None, show_traceback: bool = False):
        """记录错误日志"""
        if error:
            logger.error(f"{message}: {str(error)}")
        else:
            logger.error(message)
        print_error(message, error, show_traceback=show_traceback and self.verbose)

    def handle_import_error(self, message: str, error: Exception, stats: Dict[str, Dict[str, int]], item_type: str):
        """处理导入错误"""
        self.log_error(message, error, self.verbose)
        stats[item_type]["failed"] += 1
        if self.stop_on_error:
            raise error
