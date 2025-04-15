#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新MemoryItem表结构的主脚本

运行方式：python scripts/update_memory_schema.py
"""

import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入更新函数
from src.db.utils.update_memory_item_schema import update_memory_item_schema

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    try:
        print("开始更新MemoryItem表结构...")
        success = update_memory_item_schema()

        if success:
            print("✅ MemoryItem表结构更新成功！")
            print("\n您现在可以使用以下功能:")
            print("- 使用ID或permalink查询记忆")
            print("- 查看记忆的实体和关系统计信息")
            print("- 通过folder筛选记忆")
            print("- SQLite和向量库的同步")
        else:
            print("❌ MemoryItem表结构更新失败")
            print("请检查日志了解详细信息")
            sys.exit(1)

    except Exception as e:
        logger.error(f"更新过程中发生错误: {e}", exc_info=True)
        print(f"❌ 更新失败: {e}")
        sys.exit(1)
