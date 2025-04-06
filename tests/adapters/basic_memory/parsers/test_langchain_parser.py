#!/usr/bin/env python3
"""
LangChain解析器测试
测试LangChain知识处理器的基本功能
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from adapters.basic_memory.parsers import LangChainKnowledgeProcessor


class TestLangChainParser(unittest.TestCase):
    """测试LangChain解析器"""

    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.test_dir.name)

        # 创建测试文档
        self.test_doc_path = self.temp_dir_path / "test_doc.md"
        with open(self.test_doc_path, "w", encoding="utf-8") as f:
            f.write(
                """# 测试文档

这是一个测试文档，用于测试LangChain解析器。

## 实体示例

- 人物：张三、李四
- 概念：人工智能、机器学习
- 地点：北京、上海

## 关系示例

- 张三[认识]李四
- 人工智能[包含]机器学习
- 张三[居住于]北京
            """
            )

    def tearDown(self):
        """清理测试环境"""
        self.test_dir.cleanup()

    def test_initialization(self):
        """测试初始化"""
        processor = LangChainKnowledgeProcessor(str(self.temp_dir_path))

        # 确保对象被正确初始化
        self.assertEqual(processor.source_dir, self.temp_dir_path)
        self.assertEqual(processor.model, "gpt-4o-mini")

        # 确保数据库被正确初始化
        self.assertIsNotNone(processor.db)

    def test_process_documents_output(self):
        """测试处理文档输出"""
        processor = LangChainKnowledgeProcessor(str(self.temp_dir_path))

        # 测试输出（由于依赖模块尚未完全实现，我们只能测试输出信息）
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            processor.process_documents()

        output = f.getvalue()

        # 检查输出中是否包含预期的消息
        self.assertIn("开始处理目录", output)
        self.assertIn("LangChain解析器已恢复", output)


if __name__ == "__main__":
    unittest.main()
