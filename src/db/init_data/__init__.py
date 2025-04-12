"""
数据库初始数据包

提供数据库初始化数据
"""

import logging

from .memory_items import init_memory_items
from .rules import init_rules
from .templates import init_templates
from .workflows import init_workflows

logger = logging.getLogger(__name__)


def init_all_data():
    """初始化所有数据"""
    logger.info("开始初始化所有数据...")
    try:
        init_rules()
        init_templates()
        init_workflows()
        init_memory_items()
        logger.info("所有数据初始化完成")
    except Exception as e:
        logger.error("数据初始化过程中发生错误", exc_info=True)
        raise
