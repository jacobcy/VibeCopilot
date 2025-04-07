"""
OpenAI API客户端测试
"""

import unittest
from unittest.mock import MagicMock, patch

from adapters.content_parser.openai.api_client import OpenAIClient


class TestOpenAIClient(unittest.TestCase):
    """OpenAI API客户端测试"""

    @patch("adapters.content_parser.openai.api_client.openai")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_key")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_base")
    def test_init(self, mock_get_api_base, mock_get_api_key, mock_openai):
        """测试初始化"""
        # 设置模拟返回值
        mock_get_api_key.return_value = "test-key"
        mock_get_api_base.return_value = "https://test-api-base.com"

        # 初始化客户端
        client = OpenAIClient(model="test-model")

        # 验证初始化
        self.assertEqual(client.model, "test-model")
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.api_base, "https://test-api-base.com")
        self.assertEqual(mock_openai.api_key, "test-key")
        self.assertEqual(mock_openai.api_base, "https://test-api-base.com")

    @patch("adapters.content_parser.openai.api_client.openai")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_key")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_base")
    def test_parse_content(self, mock_get_api_base, mock_get_api_key, mock_openai):
        """测试解析内容"""
        # 设置模拟返回值
        mock_get_api_key.return_value = "test-key"
        mock_get_api_base.return_value = None

        # 模拟OpenAI API响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": "value"}'
        mock_openai.ChatCompletion.create.return_value = mock_response

        # 初始化客户端
        client = OpenAIClient()

        # 调用方法
        result = client.parse_content("system prompt", "user prompt")

        # 验证结果
        self.assertEqual(result, {"test": "value"})
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model=client.model,
            messages=[
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ],
            temperature=0.1,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

    @patch("adapters.content_parser.openai.api_client.openai")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_key")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient._get_api_base")
    @patch("adapters.content_parser.openai.api_client.OpenAIClient.parse_content")
    def test_parse_rule(self, mock_parse_content, mock_get_api_base, mock_get_api_key, mock_openai):
        """测试解析规则"""
        # 设置模拟返回值
        mock_get_api_key.return_value = "test-key"
        mock_get_api_base.return_value = None
        mock_parse_content.return_value = {"id": "test-rule"}

        # 初始化客户端
        client = OpenAIClient()

        # 调用方法
        result = client.parse_rule("rule content", "rule_context.md")

        # 验证结果
        self.assertEqual(result, {"id": "test-rule"})
        mock_parse_content.assert_called_once()

        # 检查第一个参数(system_prompt)包含规则相关指导
        self.assertIn("规则解析器", mock_parse_content.call_args[0][0])

        # 检查第二个参数(user_prompt)包含内容和上下文
        self.assertIn("rule content", mock_parse_content.call_args[0][1])
        self.assertIn("rule_context.md", mock_parse_content.call_args[0][1])


if __name__ == "__main__":
    unittest.main()
