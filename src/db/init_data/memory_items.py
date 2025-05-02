"""
Memory Item 初始数据模块

提供 Memory Item 表的初始数据
"""

import logging
from typing import Dict

from src.db import get_session
from src.db.repositories.memory_item_repository import MemoryItemRepository

logger = logging.getLogger(__name__)


def init_memory_items() -> Dict[str, int]:
    """初始化 Memory Items，并返回统计"""
    session = get_session()
    repo = MemoryItemRepository()

    success_count = 0
    fail_count = 0

    # 检查表是否为空
    if repo.count(session) == 0:
        logger.info("Memory Item 表为空，开始初始化默认数据...")
        # 添加示例 Memory Items
        items = [
            {
                "title": "示例决策",
                "content": "决定采用 FastAPI 作为后端框架。理由：性能高，异步支持好，文档完善。",
                "type": "decision",
                "tags": ["backend", "framework", "decision"],
                "source": "meeting_notes_20240115",
            },
            {
                "title": "示例问题追踪",
                "content": "用户登录在 Safari 浏览器下偶尔失败。初步判断与 cookie 处理有关。",
                "type": "issue",
                "tags": ["bug", "frontend", "login", "safari"],
                "status": "open",
            },
        ]

        for item_data in items:
            try:
                # 准备参数，将列表tags转换为逗号分隔字符串
                tags_str = ",".join(item_data.get("tags", [])) if item_data.get("tags") else None
                # 使用type作为content_type
                content_type = item_data.get("type", "text")

                repo.create_item(
                    session=session,
                    title=item_data.get("title", "无标题"),
                    content=item_data.get("content", ""),
                    tags=tags_str,
                    source=item_data.get("source"),
                    content_type=content_type,
                )
                success_count += 1
            except Exception as e:
                logger.error(f"创建 Memory Item 失败: {item_data.get('title')}", exc_info=True)
                fail_count += 1
    else:
        logger.info("Memory Item 表不为空，跳过初始化")

    logger.info(f"Memory Item 初始化完成: 成功 {success_count}, 失败 {fail_count}")
    session.close()
    return {"success": success_count, "failed": fail_count}
