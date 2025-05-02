"""
文档 Memory Item 初始化模块

从 .ai/docs 目录加载 markdown 文件，并作为 Memory Item 导入数据库。
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from src.core.config import get_app_dir
from src.memory.services.memory_item_service import MemoryItemService

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


def init_docs() -> Dict[str, int]:
    """初始化文档 Memory Items"""
    logger.info("开始初始化文档 Memory Items...")
    success_count = 0
    fail_count = 0

    doc_files = get_doc_files()
    if not doc_files:
        logger.warning("没有找到文档文件，跳过文档初始化")
        return {"success": success_count, "failed": fail_count}

    try:
        memory_service = MemoryItemService()

        for file_path_str in doc_files:
            file_path = Path(file_path_str)
            logger.info(f"正在处理文档文件: {file_path.name}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 使用文件名作为标题
                title = file_path.stem

                # 创建 MemoryItem 数据 - 现在直接传递参数
                # item_data = {
                #     "title": title,
                #     "content": content,
                #     "type": "document",  # 或者其他合适的类型
                #     "source": f"file://{file_path_str}"
                # }

                # 调用服务层方法，传递解构的参数
                created_item = memory_service.create_item(
                    title=title,
                    content=content,
                    folder="Docs",  # 指定一个文件夹
                    tags="document,init",  # 示例标签
                    permalink=None,  # 初始导入没有 permalink
                    content_type="document",  # 指定类型
                    source=f"file://{file_path_str}",
                )

                if created_item and isinstance(created_item, dict):
                    item_id = created_item.get("id")
                    item_title = created_item.get("title", "未知标题")
                    logger.info(f"成功创建 Memory Item: {item_title} (ID: {item_id})")
                    success_count += 1
                else:
                    logger.error(f"创建 Memory Item 失败: {title}")
                    fail_count += 1

            except Exception as e:
                logger.error(f"处理文档文件 {file_path.name} 时出错: {e}", exc_info=True)
                fail_count += 1

        logger.info(f"文档 Memory Items 初始化完成: 成功 {success_count}, 失败 {fail_count}")

    except Exception as e:
        logger.error(f"初始化文档 Memory Items 时出错: {e}", exc_info=True)

    return {"success": success_count, "failed": fail_count}
