#!/usr/bin/env python3
"""
使用Ollama模型解析文档的工具
提取实体、关系，并存入Basic Memory数据库
使用content_parser进行内容解析
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.basic_memory.db.memory_store import MemoryStore
from adapters.content_parser.utils.parser import parse_file


class OllamaMemoryParser:
    """使用Ollama解析文档并存入Basic Memory的解析器"""

    def __init__(self, source_dir: str, model: str = "mistral"):
        """初始化解析器

        Args:
            source_dir: 源文档目录
            model: 使用的Ollama模型名称
        """
        self.source_dir = Path(source_dir)
        self.model = model
        self.db_path = "/Users/chenyi/basic-memory/main.db"
        self.memory_store = MemoryStore(self.db_path)
        self.memory_store.setup_database()

    def _convert_to_entities(self, parse_result: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """将解析结果转换为实体关系格式

        Args:
            parse_result: 解析结果
            file_path: 文件路径

        Returns:
            Dict: 转换后的实体关系结构
        """
        rel_path = str(file_path.relative_to(self.source_dir))

        # 如果已经是实体关系格式，直接返回
        if "entities" in parse_result and "relations" in parse_result:
            # 确保文档路径正确
            for entity in parse_result.get("entities", []):
                if entity.get("type") == "document" and entity.get("name") != rel_path:
                    entity["source_path"] = rel_path
            return parse_result

        # 从文档结构中提取实体关系
        result = {
            "document_type": "document",
            "main_topic": parse_result.get("title", rel_path),
            "entities": [],
            "relations": [],
            "observations": [],
            "tags": [],
            "source_path": rel_path,
        }

        # 添加文档本身作为实体
        result["entities"].append(
            {
                "name": rel_path,
                "type": "document",
                "description": parse_result.get("description", ""),
            }
        )

        # 从块中提取实体和观察
        for block in parse_result.get("blocks", []):
            if block["type"] == "heading":
                # 添加标题作为实体
                result["entities"].append(
                    {
                        "name": block["content"],
                        "type": "concept",
                        "description": f"Level {block.get('level', 1)} heading",
                    }
                )
                # 添加文档与概念的关系
                result["relations"].append(
                    {"source": rel_path, "target": block["content"], "type": "mentions"}
                )
            elif block["type"] == "text":
                # 将文本块添加为观察
                result["observations"].append(block["content"])

        return result

    def process_documents(self) -> None:
        """处理所有文档"""
        print(f"开始处理目录: {self.source_dir}")
        processed = 0

        # 处理所有Markdown文件
        for md_file in self.source_dir.rglob("*.md"):
            print(f"解析文件: {md_file}")

            try:
                # 使用content_parser解析文件
                parse_result = parse_file(
                    str(md_file), content_type="document", parser_type="ollama", model=self.model
                )

                # 转换为实体关系格式
                entity_result = self._convert_to_entities(parse_result, md_file)

                # 存储解析结果
                self.memory_store.store_document(entity_result, md_file)

                processed += 1
                print(f"✓ 已处理: {md_file}")

            except Exception as e:
                print(f"处理文件 {md_file} 时出错: {e}")

        print(f"\n导入完成! 共处理了 {processed} 个文件。")
        print(f"数据已存储到: {self.db_path}")

        # 打印统计信息
        self.memory_store.print_stats()


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python ollama_parser.py <source_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    if not os.path.isdir(source_dir):
        print(f"错误: 目录不存在: {source_dir}")
        sys.exit(1)

    model = "mistral"  # 默认使用mistral模型

    print(f"Basic Memory文档解析器 (使用Ollama {model}模型)")
    print("=====================================")

    try:
        parser = OllamaMemoryParser(source_dir, model)
        parser.process_documents()
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
