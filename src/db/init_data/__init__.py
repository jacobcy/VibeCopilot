"""
数据库初始数据包

提供数据库初始化数据
"""

import logging
from collections import defaultdict
from typing import Dict

from .docs import init_docs
from .memory_items import init_memory_items
from .roadmaps import init_roadmaps
from .rules import init_rules
from .templates import init_templates
from .workflows import init_workflows

logger = logging.getLogger(__name__)


def init_all_data() -> Dict[str, Dict[str, int]]:
    """初始化所有数据，并返回统计信息"""
    logger.info("开始初始化所有数据...")
    results = defaultdict(lambda: {"success": 0, "failed": 0})

    try:
        results["rules"] = init_rules()
        results["templates"] = init_templates()
        results["workflows"] = init_workflows()
        results["memory_items"] = init_memory_items()
        results["roadmaps"] = init_roadmaps()
        results["docs"] = init_docs()

        total_success = sum(res["success"] for res in results.values())
        total_failed = sum(res["failed"] for res in results.values())
        logger.info(f"所有数据初始化完成: 总成功 {total_success}, 总失败 {total_failed}")

    except Exception as e:
        logger.error("数据初始化过程中发生错误", exc_info=True)
        # 可以在这里更新 results 来反映错误状态，或者直接抛出
        raise

    return dict(results)
