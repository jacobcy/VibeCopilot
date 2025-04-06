"""
OpenAI解析器测试
"""

import unittest
from unittest.mock import MagicMock, patch

from adapters.content_parser.openai.parser import OpenAIParser


class TestOpenAIParser(unittest.TestCase):
    """OpenAI解析器测试"""

    @patch("adapters.content_parser.openai.parser.OpenAIClient")
    def test_init(self, mock_client_class):
        """测试初始化"""
        # 模拟API客户端
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # 初始化解析器
        parser = OpenAIParser(model="test-model", content_type="rule")

        # 验证初始化
        self.assertEqual(parser.model, "test-model")
        self.assertEqual(parser.content_type, "rule")
        self.assertEqual(parser.api_client, mock_client)
        mock_client_class.assert_called_once_with("test-model")

    @patch("adapters.content_parser.openai.parser.OpenAIClient")
    @patch("adapters.content_parser.utils.content_template.validate_rule_structure")
    def test_parse_content_rule(self, mock_validate, mock_client_class):
        """测试解析规则内容"""
        # 模拟API客户端
        mock_client = MagicMock()
        mock_client.parse_rule.return_value = {"id": "test-rule"}
        mock_client_class.return_value = mock_client

        # 模拟验证函数永远返回True
        mock_validate.return_value = True

        # 初始化解析器
        parser = OpenAIParser(content_type="rule")

        # 调用方法
        result = parser.parse_content("rule content", "context")

        # 验证结果
        self.assertEqual(result["id"], "test-rule")
        self.assertEqual(result["content"], "rule content")
        self.assertEqual(result["path"], "context")
        mock_client.parse_rule.assert_called_once_with("rule content", "context")
        mock_validate.assert_called_once()

    @patch("adapters.content_parser.openai.parser.OpenAIClient")
    def test_parse_content_document(self, mock_client_class):
        """测试解析文档内容"""
        # 模拟API客户端
        mock_client = MagicMock()
        mock_client.parse_document.return_value = {"title": "test-doc"}
        mock_client_class.return_value = mock_client

        # 初始化解析器
        parser = OpenAIParser(content_type="document")

        # 调用方法
        result = parser.parse_content("doc content", "context")

        # 验证结果
        self.assertEqual(result["title"], "test-doc")
        self.assertEqual(result["content"], "doc content")
        self.assertEqual(result["path"], "context")
        mock_client.parse_document.assert_called_once_with("doc content", "context")

    @patch("adapters.content_parser.openai.parser.OpenAIClient")
    def test_parse_content_generic(self, mock_client_class):
        """测试解析通用内容"""
        # 模拟API客户端
        mock_client = MagicMock()
        mock_client.parse_generic.return_value = {"title": "test-generic"}
        mock_client_class.return_value = mock_client

        # 初始化解析器
        parser = OpenAIParser(content_type="generic")

        # 调用方法
        result = parser.parse_content("generic content", "context")

        # 验证结果
        self.assertEqual(result["title"], "test-generic")
        self.assertEqual(result["content"], "generic content")
        self.assertEqual(result["path"], "context")
        mock_client.parse_generic.assert_called_once_with("generic content", "context")

    @patch("adapters.content_parser.openai.parser.OpenAIClient")
    def test_parse_content_exception(self, mock_client_class):
        """测试解析内容异常"""
        # 模拟API客户端
        mock_client = MagicMock()
        mock_client.parse_rule.side_effect = Exception("API错误")
        mock_client_class.return_value = mock_client

        # 初始化解析器
        parser = OpenAIParser(content_type="rule")

        # 调用方法
        result = parser.parse_content("rule content", "context.md")

        # 验证结果是默认值
        self.assertEqual(result["id"], "context")
        self.assertEqual(result["path"], "context.md")


if __name__ == "__main__":
    unittest.main()
