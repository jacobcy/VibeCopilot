#!/usr/bin/env python3
"""
使用Ollama Mistral模型解析文档的工具
提取实体、关系，并存入Basic Memory数据库
"""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


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
        self._setup_db()

    def _setup_db(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 删除现有表
        c.execute("DROP TABLE IF EXISTS entities")
        c.execute("DROP TABLE IF EXISTS observations")
        c.execute("DROP TABLE IF EXISTS relations")

        # 创建新表
        c.execute(
            """
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            metadata TEXT
        )"""
        )

        c.execute(
            """
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER,
            content TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )"""
        )

        c.execute(
            """
        CREATE TABLE relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            target_id INTEGER,
            type TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (source_id) REFERENCES entities (id),
            FOREIGN KEY (target_id) REFERENCES entities (id)
        )"""
        )

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def _parse_with_ollama(self, content: str, file_path: str) -> Dict[str, Any]:
        """使用Ollama解析文档内容

        Args:
            content: 文档内容
            file_path: 文件路径，用于上下文

        Returns:
            Dict: 包含解析结果的字典
        """
        rel_path = file_path.relative_to(self.source_dir)

        # 构建提示词
        prompt = f"""分析以下Markdown文档，提取主要实体和关系。

文档路径: {rel_path}

文档内容:
{content[:6000]}  # 限制长度防止超出上下文窗口

请执行以下任务:
1. 识别文档中的主要概念、实体、组件和技术
2. 确定这些实体之间的关系
3. 提取主要观察点和见解
4. 确定文档的类型和主题

以严格的JSON格式返回结果，格式如下:
{{
  "document_type": "文档类型，如指南、架构、研究等",
  "main_topic": "文档的主要主题",
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型，如组件、概念、技术、人物等",
      "description": "简短描述"
    }}
  ],
  "relations": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称",
      "type": "关系类型，如包含、使用、依赖等"
    }}
  ],
  "observations": [
    "关键观察点1",
    "关键观察点2"
  ],
  "tags": ["标签1", "标签2"]
}}

只返回JSON，不要有其他文本。
"""

        # 调用Ollama
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True
            )

            # 提取JSON部分
            output = result.stdout.strip()
            json_start = output.find("{")
            json_end = output.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"解析JSON失败: {e}")
                    print(f"原始JSON字符串: {json_str}")
                    return self._get_default_result(rel_path)
            else:
                print(f"无法从输出中提取JSON: {output}")
                return self._get_default_result(rel_path)

        except subprocess.CalledProcessError as e:
            print(f"调用Ollama失败: {e}")
            print(f"错误输出: {e.stderr}")
            return self._get_default_result(rel_path)

    def _get_default_result(self, file_path: str) -> Dict[str, Any]:
        """当解析失败时返回默认结果

        Args:
            file_path: 文件路径

        Returns:
            Dict: 默认的解析结果
        """
        return {
            "document_type": "unknown",
            "main_topic": str(file_path),
            "entities": [
                {"name": str(file_path), "type": "document", "description": "Markdown document"}
            ],
            "relations": [],
            "observations": ["文档内容无法解析"],
            "tags": [],
        }

    def _store_parse_result(self, result: Dict[str, Any], file_path: str, content: str) -> None:
        """存储解析结果到数据库

        Args:
            result: 解析结果
            file_path: 文件路径
            content: 原始文档内容
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 1. 创建文档实体
        rel_path = str(file_path.relative_to(self.source_dir))
        doc_metadata = {
            "document_type": result.get("document_type", "unknown"),
            "main_topic": result.get("main_topic", ""),
            "source_path": rel_path,
            "tags": result.get("tags", []),
        }

        c.execute(
            "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
            (rel_path, "document", json.dumps(doc_metadata)),
        )
        doc_id = c.lastrowid

        # 2. 存储原始内容作为观察
        c.execute(
            "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
            (doc_id, content, json.dumps({"type": "original_content"})),
        )

        # 3. 存储提取的观察
        for i, obs in enumerate(result.get("observations", [])):
            c.execute(
                "INSERT INTO observations (entity_id, content, metadata) VALUES (?, ?, ?)",
                (doc_id, obs, json.dumps({"type": "extracted_observation", "order": i})),
            )

        # 4. 创建提取的实体
        entity_ids = {}  # 存储实体名称到ID的映射
        entity_ids[rel_path] = doc_id  # 添加文档自身

        for entity in result.get("entities", []):
            entity_name = entity.get("name", "")
            if not entity_name or entity_name == rel_path:
                continue

            entity_metadata = {
                "type": entity.get("type", "concept"),
                "description": entity.get("description", ""),
                "source_document": rel_path,
            }

            # 检查实体是否已存在
            c.execute("SELECT id FROM entities WHERE title = ?", (entity_name,))
            existing = c.fetchone()

            if existing:
                entity_ids[entity_name] = existing[0]
            else:
                c.execute(
                    "INSERT INTO entities (title, type, metadata) VALUES (?, ?, ?)",
                    (entity_name, "concept", json.dumps(entity_metadata)),
                )
                entity_ids[entity_name] = c.lastrowid

        # 5. 创建关系
        for relation in result.get("relations", []):
            source_name = relation.get("source", "")
            target_name = relation.get("target", "")
            rel_type = relation.get("type", "related_to")

            if not source_name or not target_name:
                continue

            # 确保两个实体都存在
            if source_name not in entity_ids:
                print(f"警告：关系源实体 '{source_name}' 未找到，跳过")
                continue

            if target_name not in entity_ids:
                print(f"警告：关系目标实体 '{target_name}' 未找到，跳过")
                continue

            # 创建关系
            c.execute(
                "INSERT INTO relations (source_id, target_id, type, metadata) VALUES (?, ?, ?, ?)",
                (
                    entity_ids[source_name],
                    entity_ids[target_name],
                    rel_type,
                    json.dumps({"source_document": rel_path}),
                ),
            )

        # 6. 创建文档与提取实体的关系
        for entity_name, entity_id in entity_ids.items():
            if entity_name != rel_path:  # 不要创建自引用
                c.execute(
                    "INSERT INTO relations (source_id, target_id, type, metadata) VALUES (?, ?, ?, ?)",
                    (doc_id, entity_id, "mentions", json.dumps({"automatic": True})),
                )

        conn.commit()
        conn.close()

    def process_documents(self) -> None:
        """处理所有文档"""
        print(f"开始处理目录: {self.source_dir}")
        processed = 0

        # 处理所有Markdown文件
        for md_file in self.source_dir.rglob("*.md"):
            print(f"解析文件: {md_file}")

            try:
                # 读取文件内容
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 使用Ollama解析
                parse_result = self._parse_with_ollama(content, md_file)

                # 存储解析结果
                self._store_parse_result(parse_result, md_file, content)

                processed += 1
                print(f"✓ 已处理: {md_file}")

            except Exception as e:
                print(f"处理文件 {md_file} 时出错: {e}")

        print(f"\n导入完成! 共处理了 {processed} 个文件。")
        print(f"数据已存储到: {self.db_path}")

        # 打印统计信息
        self._print_stats()

    def _print_stats(self) -> None:
        """打印数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 获取实体数量
        c.execute("SELECT COUNT(*) FROM entities")
        entity_count = c.fetchone()[0]

        # 获取观察数量
        c.execute("SELECT COUNT(*) FROM observations")
        observation_count = c.fetchone()[0]

        # 获取关系数量
        c.execute("SELECT COUNT(*) FROM relations")
        relation_count = c.fetchone()[0]

        # 获取实体类型统计
        c.execute("SELECT type, COUNT(*) FROM entities GROUP BY type")
        type_stats = c.fetchall()

        conn.close()

        print("\n数据库统计信息:")
        print(f"- 实体总数: {entity_count}")
        print(f"- 观察总数: {observation_count}")
        print(f"- 关系总数: {relation_count}")

        print("\n实体类型分布:")
        for type_name, count in type_stats:
            print(f"- {type_name}: {count}")


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
