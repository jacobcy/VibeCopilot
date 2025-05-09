"""
文档 Memory Item 初始化模块

从 .ai/docs 目录加载 markdown 文件，并作为 Memory Item 导入数据库。
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from src.core.config import get_app_dir
from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


def get_doc_files() -> List[str]:
    """获取文档文件列表 (.md)

    Returns:
        List[str]: 文档文件路径列表
    """
    docs_dir = Path(get_app_dir()) / ".ai" / "docs"

    if not docs_dir.exists():
        logger.warning(f"文档目录不存在: {docs_dir}")
        return []

    # 获取所有 .md 文件
    md_files = list(docs_dir.glob("*.md"))

    return [str(file) for file in md_files]


def init_docs(session) -> Dict[str, int]:
    """初始化文档 Memory Items"""
    logger.info("开始初始化文档 Memory Items...")
    success_count = 0
    fail_count = 0

    doc_files = get_doc_files()
    if not doc_files:
        logger.warning("没有找到文档文件，跳过文档初始化")
        return {"success": success_count, "failed": fail_count}

    try:
        memory_service = MemoryService()

        for file_path_str in doc_files:
            file_path = Path(file_path_str)
            logger.info(f"正在处理文档文件: {file_path.name}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 使用文件名作为标题
                title = file_path.stem

                # 修改：使用create_note方法而不是create_item
                success, message, result = memory_service.create_note(content=content, title=title, folder="docs", tags="document,init")

                if success:
                    logger.info(f"成功创建 Memory Item: {title}, 消息: {message}")
                    success_count += 1
                else:
                    logger.error(f"创建 Memory Item 失败: {title}, 错误: {message}")
                    fail_count += 1

            except Exception as e:
                logger.error(f"处理文档文件 {file_path.name} 时出错: {e}", exc_info=True)
                fail_count += 1

        logger.info(f"文档 Memory Items 初始化完成: 成功 {success_count}, 失败 {fail_count}")

    except Exception as e:
        logger.error(f"初始化文档 Memory Items 时出错: {e}", exc_info=True)

    return {"success": success_count, "failed": fail_count}
