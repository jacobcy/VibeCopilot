"""
Memory Item 初始数据模块

提供 Memory Item 表的初始数据
"""

import logging
from typing import Dict

from src.memory.services.memory_service import get_memory_service

logger = logging.getLogger(__name__)


def init_memory_items() -> Dict[str, int]:
    """初始化 Memory Items，并返回统计"""
    success_count = 0
    fail_count = 0

    # 使用单例模式获取 MemoryService 实例
    memory_service = get_memory_service()

    # 检查是否需要初始化
    success, _, result = memory_service.list_notes()
    if not success or not result:
        logger.info("Memory Item 表为空，开始初始化默认数据...")

        # 添加示例 Memory Items
        items_data = [
            {
                "title": "示例决策",
                "content": "决定采用 FastAPI 作为后端框架。理由：性能高，异步支持好，文档完善。",
                "folder": "decision",
                "tags": "backend,framework,decision",
            },
            {
                "title": "示例问题追踪",
                "content": "用户登录在 Safari 浏览器下偶尔失败。初步判断与 cookie 处理有关。",
                "folder": "issue",
                "tags": "bug,frontend,login,safari",
            },
            {
                "title": "开发指南",
                "content": "VibeCopilot 开发指南：\n\n1. 所有代码必须通过单元测试\n2. 遵循 PEP 8 编码规范\n3. 提交前使用 black 格式化代码",
                "folder": "docs",
                "tags": "guide,development,standards",
            },
        ]

        for item_data in items_data:
            try:
                success, message, _ = memory_service.create_note(
                    content=item_data["content"], title=item_data["title"], folder=item_data["folder"], tags=item_data.get("tags", "")
                )

                if success:
                    logger.info(f"成功创建初始化记忆条目: {item_data['title']}")
                    success_count += 1
                else:
                    logger.error(f"创建记忆条目失败: {item_data['title']}, 错误: {message}")
                    fail_count += 1
            except Exception as e:
                logger.error(f"创建记忆条目时出错: {item_data['title']}", exc_info=True)
                fail_count += 1
    else:
        logger.info("Memory Item 表不为空，跳过初始化")

    logger.info(f"Memory Item 初始化完成: 成功 {success_count}, 失败 {fail_count}")
    return {"success": success_count, "failed": fail_count}
