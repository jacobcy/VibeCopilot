#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Roadmap同步功能
"""

import unittest
from unittest.mock import MagicMock, patch

from src.sync.github_sync import GitHubSyncService
from src.sync.yaml_sync import YamlSyncService


class TestRoadmapSync(unittest.TestCase):
    """测试Roadmap同步功能"""

    def test_yaml_sync_service_init(self):
        """测试YAML同步服务初始化"""
        # 创建模拟对象
        mock_service = MagicMock()

        # 初始化服务
        yaml_sync = YamlSyncService(mock_service)

        # 验证引用关系
        self.assertEqual(yaml_sync.service, mock_service)

    @patch("src.sync.yaml_sync.os.path.exists")
    @patch("os.path.join")
    def test_yaml_sync_export(self, mock_join, mock_exists):
        """测试YAML同步导出功能"""
        # 设置模拟
        mock_service = MagicMock()
        mock_service.get_roadmap.return_value = {"id": "roadmap1", "name": "测试路线图", "description": "测试描述"}

        mock_exists.return_value = True
        mock_join.return_value = "/path/to/output.yaml"

        # 初始化服务
        yaml_sync = YamlSyncService(mock_service)

        # 测试导出
        result = yaml_sync.export_to_yaml("roadmap1", output_path="/path/to/output.yaml")

        # 验证调用 - 移除strict=True参数，允许多次调用
        mock_service.get_roadmap.assert_called_with("roadmap1")
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], "roadmap1")
        self.assertEqual(result["file_path"], "/path/to/output.yaml")

    @patch("src.sync.yaml_sync.os.path.exists")
    def test_yaml_sync_import(self, mock_exists):
        """测试YAML同步导入功能"""
        # 设置模拟
        mock_service = MagicMock()
        mock_service.create_roadmap.return_value = {"success": True, "roadmap_id": "new-roadmap", "roadmap_name": "Test Roadmap"}

        mock_exists.return_value = True

        # 初始化服务
        yaml_sync = YamlSyncService(mock_service)

        # 测试导入
        result = yaml_sync.import_from_yaml("/path/to/test_roadmap.yaml")

        # 验证调用
        self.assertTrue(result["success"])
        self.assertEqual(result["source_file"], "/path/to/test_roadmap.yaml")

    def test_github_sync_service_init(self):
        """测试GitHub同步服务初始化"""
        # 创建模拟对象
        mock_service = MagicMock()

        # 初始化服务
        with patch("src.sync.github_sync.GitHubApiFacade") as mock_github_api:
            mock_api_instance = MagicMock()
            mock_github_api.return_value = mock_api_instance

            github_sync = GitHubSyncService(mock_service)

            # 验证引用关系 - 使用正确的属性名
            self.assertEqual(github_sync.roadmap_service, mock_service)
            self.assertIsNotNone(github_sync.api_facade)


if __name__ == "__main__":
    unittest.main()
