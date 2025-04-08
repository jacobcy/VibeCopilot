"""
RuleProcessor 测试模块

测试规则处理器的各项功能
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.parsing.processors.rule_processor import RuleProcessor


class TestRuleProcessor:
    """测试RuleProcessor类的各项功能"""

    @pytest.fixture
    def rule_processor(self):
        """创建规则处理器实例作为测试固定装置"""
        # 使用正则表达式后端以避免调用外部API
        return RuleProcessor(backend="regex")

    @pytest.fixture
    def sample_rule_content(self):
        """提供示例规则内容作为测试固定装置"""
        return """---
type: test
description: 测试规则
tags: test,rule
---

# 测试规则

## 描述
这是一个测试规则。

## 示例
<example>
示例内容
</example>
"""

    @pytest.fixture
    def sample_rule_file(self, sample_rule_content):
        """创建示例规则文件作为测试固定装置"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        # 创建临时文件
        file_path = os.path.join(temp_dir, "test_rule.mdc")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sample_rule_content)

        yield file_path

        # 清理
        shutil.rmtree(temp_dir)

    def test_process_rule_text(self, rule_processor, sample_rule_content):
        """测试处理规则文本"""
        # 处理规则文本
        result = rule_processor.process_rule_text(sample_rule_content)

        # 验证结果
        assert result["title"] == "测试规则"
        assert "front_matter" in result
        assert result["front_matter"]["type"] == "test"
        assert result["front_matter"]["description"] == "测试规则"
        assert "validation" in result
        assert result["validation"]["valid"] is True

    def test_process_rule_file(self, rule_processor, sample_rule_file):
        """测试处理规则文件"""
        # 处理规则文件
        result = rule_processor.process_rule_file(sample_rule_file)

        # 验证结果
        assert "success" in result or "title" in result
        if "success" in result:
            assert result["success"] is True

        assert "file_info" in result
        assert result["file_info"]["path"] == sample_rule_file
        assert result["file_info"]["name"] == os.path.basename(sample_rule_file)

    def test_process_rule_directory(self, rule_processor, sample_rule_file):
        """测试处理规则目录"""
        # 获取目录路径
        directory = os.path.dirname(sample_rule_file)

        # 处理规则目录
        results = rule_processor.process_rule_directory(directory, pattern="*.mdc")

        # 验证结果
        assert len(results) == 1
        assert results[0]["file_info"]["path"] == sample_rule_file

    def test_extract_rule_metadata(self, rule_processor, sample_rule_file):
        """测试提取规则元数据"""
        # 处理规则文件
        rule_result = rule_processor.process_rule_file(sample_rule_file)

        # 提取元数据
        metadata = rule_processor.extract_rule_metadata(rule_result)

        # 验证结果
        assert metadata["title"] == "测试规则"
        assert metadata["type"] == "test"
        assert metadata["description"] == "测试规则"
        assert "test" in metadata["tags"]
        assert metadata["valid"] is True
        assert "file_path" in metadata
        assert metadata["file_path"] == sample_rule_file

    def test_validate_rule_structure(self, rule_processor):
        """测试验证规则结构"""
        # 有效的规则
        valid_rule = {"title": "测试规则", "front_matter": {"type": "test", "description": "测试规则"}}
        assert rule_processor._validate_rule_structure(valid_rule) is True

        # 无标题的规则
        invalid_rule_1 = {"front_matter": {"type": "test", "description": "测试规则"}}
        assert rule_processor._validate_rule_structure(invalid_rule_1) is False

        # 无类型的规则
        invalid_rule_2 = {"title": "测试规则", "front_matter": {"description": "测试规则"}}
        assert rule_processor._validate_rule_structure(invalid_rule_2) is False

    def test_missing_file_handling(self, rule_processor):
        """测试处理不存在的文件"""
        # 处理不存在的文件
        result = rule_processor.process_rule_file("/path/to/non_existent_file.mdc")

        # 验证结果
        assert result["success"] is False
        assert "error" in result

    def test_invalid_directory_handling(self, rule_processor):
        """测试处理不存在的目录"""
        # 处理不存在的目录
        results = rule_processor.process_rule_directory("/path/to/non_existent_directory")

        # 验证结果
        assert len(results) == 1
        assert results[0]["success"] is False
        assert "error" in results[0]
