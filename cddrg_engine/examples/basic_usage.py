#!/usr/bin/env python
"""CDDRG引擎基本用法示例."""

import os

# 添加项目根目录到系统路径
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cddrg_engine import Engine, EngineConfig


def main():
    """演示CDDRG引擎的基本用法."""
    print("=== CDDRG引擎基本用法示例 ===")

    # 1. 创建引擎配置
    config = EngineConfig(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        vector_store_path="./examples/vector_store",
        model_adapter="openai",
        debug_mode=True,
        log_level="DEBUG",
    )

    # 2. 初始化引擎
    print("\n初始化引擎...")
    engine = Engine(config)

    # 3. 获取引擎状态
    print("\n引擎状态:")
    status = engine.get_status()
    for key, value in status.items():
        if key == "config":
            print(f"  {key}: <配置对象>")
        else:
            print(f"  {key}: {value}")

    # 4. 添加示例知识
    print("\n添加知识...")
    knowledge_id = engine.add_knowledge(
        content="规则应简洁明了，避免冗余。每条规则专注于单一方面。",
        metadata={"type": "rule", "category": "style", "tags": ["writing", "convention"]},
    )
    print(f"知识添加成功，ID: {knowledge_id}")

    # 5. 生成规则
    print("\n生成规则...")
    context = "用户正在编写技术文档，需要遵循规范"
    task = "提供文档编写建议"

    rule = engine.generate_rule(context, task)
    print(f"规则ID: {rule['id']}")
    print(f"规则内容: {rule['content']}")
    print(f"创建时间: {rule['created_at']}")

    # 6. 查询知识库
    print("\n查询知识库...")
    results = engine.query("文档编写规范", filters={"type": "rule"})
    print(f"查询结果数量: {len(results)}")


if __name__ == "__main__":
    main()
