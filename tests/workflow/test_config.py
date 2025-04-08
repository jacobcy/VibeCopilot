#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流配置模块

验证工作流配置的基本功能
"""

import os
from pathlib import Path
from unittest import mock

import pytest

from src.workflow.config import TEMPLATE_DIR, get_template_path, list_templates


class TestWorkflowConfig:
    """工作流配置测试类"""

    def test_get_template_path_with_extension(self):
        """测试获取带扩展名的模板路径"""
        template_name = "test_flow.json"
        expected_path = os.path.join(TEMPLATE_DIR, template_name)
        path = get_template_path(template_name)
        assert path == expected_path

    def test_get_template_path_without_extension(self):
        """测试获取不带扩展名的模板路径"""
        template_name = "test_flow"
        expected_path = os.path.join(TEMPLATE_DIR, template_name + ".json")
        path = get_template_path(template_name)
        assert path == expected_path

    @mock.patch("os.path.exists")
    @mock.patch("os.listdir")
    def test_list_templates_directory_exists(self, mock_listdir, mock_exists):
        """测试列出模板，目录存在的情况"""
        # 配置模拟行为
        mock_exists.return_value = True
        mock_listdir.return_value = ["template1.json", "template2.json", "not_a_template.txt"]

        # 执行测试
        templates = list_templates()

        # 验证结果
        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates
        assert "not_a_template" not in templates

    @mock.patch("os.path.exists")
    def test_list_templates_directory_not_exists(self, mock_exists):
        """测试列出模板，目录不存在的情况"""
        # 配置模拟行为
        mock_exists.return_value = False

        # 执行测试
        templates = list_templates()

        # 验证结果
        assert templates == []
