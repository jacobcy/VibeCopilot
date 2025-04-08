#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Roadmap服务功能
"""

import unittest
from unittest.mock import MagicMock, patch

from src.roadmap.service.roadmap_service import RoadmapService


class TestRoadmapService(unittest.TestCase):
    """测试Roadmap服务功能"""

    @patch("src.roadmap.sync.GitHubSyncService")
    @patch("src.roadmap.sync.YamlSyncService")
    def test_init_roadmap_service(self, mock_yaml_sync, mock_github_sync):
        """测试初始化路线图服务"""
        # 设置模拟对象
        mock_github_instance = MagicMock()
        mock_yaml_instance = MagicMock()
        mock_github_sync.return_value = mock_github_instance
        mock_yaml_sync.return_value = mock_yaml_instance

        # 测试初始化
        mock_session = MagicMock()
        service = RoadmapService(session=mock_session)

        # 验证同步服务创建
        mock_github_sync.assert_called_once_with(service)
        mock_yaml_sync.assert_called_once_with(service)
        self.assertEqual(service.github_sync, mock_github_instance)
        self.assertEqual(service.yaml_sync, mock_yaml_instance)

    def test_get_roadmap(self):
        """测试获取路线图"""
        # 设置模拟对象
        mock_get_roadmap = MagicMock()
        mock_get_roadmap.return_value = {"id": "roadmap1", "name": "测试路线图"}

        # 初始化服务
        service = RoadmapService()
        # 替换委托方法
        service.get_roadmap = mock_get_roadmap

        # 测试获取路线图
        roadmap = service.get_roadmap("roadmap1")

        # 验证调用
        mock_get_roadmap.assert_called_once_with("roadmap1")
        self.assertEqual(roadmap, {"id": "roadmap1", "name": "测试路线图"})

    @patch("src.roadmap.service.roadmap_service.get_roadmaps")
    def test_get_all_roadmaps(self, mock_get_roadmaps):
        """测试获取所有路线图"""
        # 设置模拟对象
        mock_get_roadmaps.return_value = [{"id": "roadmap1", "name": "路线图1"}, {"id": "roadmap2", "name": "路线图2"}]

        # 初始化服务
        service = RoadmapService()
        service._active_roadmap_id = "roadmap1"  # 设置活跃路线图ID

        # 测试列出所有路线图
        result = service.list_roadmaps()

        # 验证调用
        mock_get_roadmaps.assert_called_once_with(service)
        self.assertTrue(result["success"])
        self.assertEqual(result["active_id"], "roadmap1")
        self.assertEqual(len(result["roadmaps"]), 2)
        self.assertEqual(result["roadmaps"][0]["id"], "roadmap1")
        self.assertEqual(result["roadmaps"][1]["id"], "roadmap2")

    def test_sync_roadmap(self):
        """测试同步路线图"""
        # 设置模拟对象
        mock_sync_from_github = MagicMock()
        mock_sync_from_github.return_value = {"success": True, "message": "同步成功"}

        # 初始化服务
        service = RoadmapService()
        # 替换委托方法
        service.sync_from_github = mock_sync_from_github

        # 测试同步路线图
        result = service.sync_from_github()

        # 验证调用
        mock_sync_from_github.assert_called_once()
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "同步成功")

    def test_create_roadmap(self):
        """测试创建路线图"""
        # 设置模拟对象
        mock_create_roadmap = MagicMock()
        mock_create_roadmap.return_value = {"success": True, "roadmap_id": "new-roadmap", "roadmap_name": "新路线图"}

        # 初始化服务
        service = RoadmapService()
        # 替换委托方法
        service.create_roadmap = mock_create_roadmap

        # 测试创建路线图 - 使用正确的参数格式
        name = "新路线图"
        description = "测试描述"
        result = service.create_roadmap(name=name, description=description)

        # 验证调用
        mock_create_roadmap.assert_called_once_with(name=name, description=description)
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], "new-roadmap")


if __name__ == "__main__":
    unittest.main()
