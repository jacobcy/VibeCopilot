#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite与向量库集成示例

展示SQLite与向量库的集成功能
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.db import get_session
from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.memory.memory_manager import MemoryManager

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def run_integration_example():
    """运行SQLite与向量库集成示例"""
    print("\n===== SQLite与向量库集成示例 =====\n")

    # 初始化
    memory_manager = MemoryManager()
    session = get_session()
    memory_item_repo = MemoryItemRepository(session)

    # 1. 存储新记忆
    print("\n[1] 存储新记忆...")
    result = await memory_manager.store_memory(
        content="向量库是一种专门用于存储和检索向量的数据库系统。它特别适用于存储语义嵌入，支持相似度搜索。ChromaDB是一种简单易用的向量数据库，可以通过pip安装，无需复杂的依赖。",
        title="向量库简介",
        tags="向量库,ChromaDB,嵌入,数据库",
        folder="knowledge",
    )

    if result["success"]:
        print(f"✅ 记忆存储成功 - ID: {result['memory_item_id']}, Permalink: {result['permalink']}")
        permalink = result["permalink"]
        memory_item_id = result["memory_item_id"]
    else:
        print(f"❌ 记忆存储失败: {result['message']}")
        return

    # 2. 从SQLite获取记忆
    print("\n[2] 从SQLite获取记忆...")
    memory_item = memory_item_repo.get_by_id(memory_item_id)

    if memory_item:
        print(f"✅ 从SQLite获取成功:")
        print(f"  - 标题: {memory_item.title}")
        print(f"  - 内容: {memory_item.content[:50]}...")
        print(f"  - 实体数: {memory_item.entity_count}")
        print(f"  - 关系数: {memory_item.relation_count}")
        print(f"  - Permalink: {memory_item.permalink}")
    else:
        print("❌ 从SQLite获取失败")

    # 3. 从向量库获取记忆
    print("\n[3] 从向量库获取记忆...")
    result = await memory_manager.get_memory_by_id(permalink)

    if result["success"]:
        print("✅ 从向量库获取成功:")
        memory = result["memory"]
        print(f"  - 标题: {memory['title']}")
        print(f"  - 内容: {memory['content'][:50]}...")
        print(f"  - SQLite ID: {memory.get('memory_item_id')}")
    else:
        print(f"❌ 从向量库获取失败: {result['message']}")

    # 4. 搜索记忆
    print("\n[4] 搜索记忆...")
    search_result = await memory_manager.retrieve_memory("ChromaDB是什么")

    if search_result["success"] and search_result.get("memories"):
        print("✅ 搜索成功:")
        for i, memory in enumerate(search_result["memories"]):
            print(f"  结果 {i+1}:")
            print(f"  - 标题: {memory['title']}")
            print(f"  - 相关度: {memory.get('score', 0):.2f}")
            print(f"  - SQLite ID: {memory.get('memory_item_id')}")
            print()
    else:
        print("❌ 搜索失败或无结果")

    # 5. 按ID或permalink更新记忆
    print("\n[5] 更新记忆 (通过ID)...")

    # 先获取并输出原记忆
    memory_item_before = memory_item_repo.get_by_id(memory_item_id)
    print(f"更新前内容: {memory_item_before.content[:50]}...")

    # 删除原记忆并创建新记忆
    delete_result = await memory_manager.delete_memory(permalink)

    if delete_result["success"]:
        # 创建更新后的记忆
        result = await memory_manager.store_memory(
            content="向量库是专门设计用于高效存储和检索向量数据的数据库系统。它在机器学习和人工智能领域有广泛应用，特别是在需要相似性搜索的场景。ChromaDB是一种开源向量数据库，具有易用性和高性能的特点。",
            title="向量库简介（更新版）",
            tags="向量库,ChromaDB,相似度搜索,机器学习",
            folder="knowledge",
        )

        if result["success"]:
            print(f"✅ 记忆更新成功 - 新ID: {result['memory_item_id']}, 新Permalink: {result['permalink']}")

            # 获取更新后的记忆
            memory_item_after = memory_item_repo.get_by_id(result["memory_item_id"])
            print(f"更新后内容: {memory_item_after.content[:50]}...")
        else:
            print(f"❌ 更新失败: {result['message']}")
    else:
        print(f"❌ 删除原记忆失败: {delete_result['message']}")

    print("\n===== 示例结束 =====\n")


if __name__ == "__main__":
    asyncio.run(run_integration_example())
