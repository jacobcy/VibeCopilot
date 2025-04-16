"""
记忆项初始数据模块

提供记忆项表的初始数据
"""

import json
import logging
from datetime import datetime

from src.core.config import refresh_config
from src.db import get_session
from src.db.repositories.memory_item_repository import MemoryItemRepository

logger = logging.getLogger(__name__)


def init_memory_items():
    """初始化记忆项数据"""
    # 刷新配置
    refresh_config()

    session = get_session()
    repo = MemoryItemRepository(session)

    # 添加一些示例记忆项
    items = [
        {
            "title": "项目初始化记录",
            "content": "VibeCopilot项目于2025年4月12日初始化，采用Python+React技术栈。",
            "content_type": "note",
            "tags": ["项目", "初始化", "技术栈"],
            "source": "系统初始化",
        },
        {
            "title": "数据库设计文档",
            "content": "数据库采用SQLite作为存储引擎，主要包含规则、模板、工作流等核心表。",
            "content_type": "document",
            "tags": ["数据库", "设计", "文档"],
            "source": "技术文档",
        },
        {
            "title": "开发规范说明",
            "content": "项目遵循PEP8规范，使用black进行代码格式化，所有函数必须有文档字符串。",
            "content_type": "document",
            "tags": ["规范", "开发", "文档"],
            "source": "开发文档",
        },
    ]

    success_count = 0
    for item in items:
        try:
            # 使用专用的create_item方法创建记忆项
            repo.create_item(
                title=item["title"],
                content=item["content"],
                content_type=item["content_type"],
                tags=",".join(item["tags"]) if item["tags"] else None,
                source=item["source"],
                folder="Inbox",  # 设置默认文件夹
            )
            success_count += 1
        except Exception as e:
            logger.error(f"创建记忆项失败: {item['title']}", exc_info=True)

    logger.info(f"记忆项初始化完成: 成功 {success_count}/{len(items)}")
    session.close()
