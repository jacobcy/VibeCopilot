"""
解析器工厂测试模块
"""

import os
from unittest.mock import patch

import pytest
import rule_parser
from rule_parser.ollama_rule_parser import OllamaRuleParser
from rule_parser.openai_rule_parser import OpenAIRuleParser
from rule_parser.parser_factory import create_parser, get_default_parser


def test_create_parser_openai():
    """测试创建OpenAI解析器"""
    # 创建OpenAI解析器
    parser = create_parser("openai")

    # 验证结果
    assert isinstance(parser, OpenAIRuleParser)
    assert parser.model == os.environ.get("VIBE_OPENAI_MODEL", "gpt-4o-mini")


def test_create_parser_ollama():
    """测试创建Ollama解析器"""
    # 创建Ollama解析器
    parser = create_parser("ollama")

    # 验证结果
    assert isinstance(parser, OllamaRuleParser)
    assert parser.model == os.environ.get("VIBE_OLLAMA_MODEL", "mistral")


def test_create_parser_with_custom_model():
    """测试使用自定义模型创建解析器"""
    # 创建带自定义模型的解析器
    parser = create_parser("openai", "gpt-4")

    # 验证结果
    assert isinstance(parser, OpenAIRuleParser)
    assert parser.model == "gpt-4"


def test_create_parser_invalid_type():
    """测试创建无效类型的解析器"""
    # 尝试创建无效类型的解析器应该抛出ValueError
    with pytest.raises(ValueError):
        create_parser("invalid_type")


@patch.dict(os.environ, {"VIBE_RULE_PARSER": "openai", "OPENAI_API_KEY": "test-key"})
def test_get_default_parser_openai():
    """测试获取默认的OpenAI解析器"""
    # 获取默认解析器
    parser = get_default_parser()

    # 验证结果
    assert isinstance(parser, OpenAIRuleParser)


@patch.dict(os.environ, {"VIBE_RULE_PARSER": "ollama"})
def test_get_default_parser_ollama():
    """测试获取默认的Ollama解析器"""
    # 获取默认解析器
    parser = get_default_parser()

    # 验证结果
    assert isinstance(parser, OllamaRuleParser)


@patch.dict(os.environ, {"VIBE_RULE_PARSER": "openai"}, clear=True)
@patch("rule_parser.parser_factory._check_openai_key_in_env_file", return_value=False)
def test_get_default_parser_fallback(mock_check):
    """测试当OpenAI API密钥不可用时回退到Ollama"""
    # 获取默认解析器
    parser = get_default_parser()

    # 验证结果：应该回退到Ollama解析器
    assert isinstance(parser, OllamaRuleParser)


@patch(
    "builtins.open",
    side_effect=lambda *args, **kwargs: {
        ".env": mock_open(read_data="OPENAI_API_KEY=test-key")
    }.get(args[0], mock_open())(args[0]),
)
def test_check_openai_key_in_env_file_exists(mock_open):
    """测试.env文件中存在OpenAI API密钥"""
    from rule_parser.parser_factory import _check_openai_key_in_env_file

    # 检查.env文件中是否有API密钥
    result = _check_openai_key_in_env_file()

    # 验证结果
    assert result is True


@patch(
    "builtins.open",
    side_effect=lambda *args, **kwargs: {".env": mock_open(read_data="OTHER_KEY=value")}.get(
        args[0], mock_open()
    )(args[0]),
)
def test_check_openai_key_in_env_file_not_exists(mock_open):
    """测试.env文件中不存在OpenAI API密钥"""
    from rule_parser.parser_factory import _check_openai_key_in_env_file

    # 检查.env文件中是否有API密钥
    result = _check_openai_key_in_env_file()

    # 验证结果
    assert result is False


@patch("builtins.open", side_effect=FileNotFoundError)
def test_check_openai_key_in_env_file_no_file(mock_open):
    """测试.env文件不存在"""
    from rule_parser.parser_factory import _check_openai_key_in_env_file

    # 检查.env文件中是否有API密钥
    result = _check_openai_key_in_env_file()

    # 验证结果
    assert result is False
