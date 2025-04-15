"""
测试文档处理器
"""

import os
import sys
import unittest

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.parsing.processors.document_processor import DocumentProcessor
from src.parsing.prompt_templates import get_prompt_template, get_system_prompt


class TestDocumentProcessor(unittest.TestCase):
    """测试文档处理器"""

    def setUp(self):
        """测试准备"""
        self.processor = DocumentProcessor(backend="openai", config={"provider": "openai"})

        # 简单的测试文档
        self.test_document = """# 测试文档

## 第一章

这是测试文档的第一章内容。

## 第二章

这是测试文档的第二章内容。
"""

    def test_processor_initialization(self):
        """测试处理器初始化"""
        self.assertEqual(self.processor.backend, "openai")
        self.assertIsNotNone(self.processor.parser)

    def test_system_prompt_integration(self):
        """测试系统提示集成"""
        # 获取文档类型的系统提示
        system_prompt = get_system_prompt("document")
        self.assertTrue("文档分析专家" in system_prompt)

    def test_user_prompt_integration(self):
        """测试用户提示集成"""
        # 获取文档类型的用户提示
        user_prompt = get_prompt_template("document")
        self.assertTrue("Parse the following document content" in user_prompt)

    def test_document_text_processing(self):
        """测试文档文本处理"""
        # 模拟解析器解析结果
        self.processor.parser.parse = lambda content, content_type: {
            "success": True,
            "title": "测试文档",
            "content": content,
            "structure": {"headings": [{"level": 1, "text": "测试文档"}, {"level": 2, "text": "第一章"}, {"level": 2, "text": "第二章"}]},
            "metadata": {"word_count": len(content.split()), "line_count": len(content.split("\n"))},
        }

        # 处理文档
        result = self.processor.process_document_text(self.test_document)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["title"], "测试文档")
        self.assertEqual(len(result["structure"]["headings"]), 3)


if __name__ == "__main__":
    unittest.main()
