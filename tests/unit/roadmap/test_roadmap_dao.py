#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Roadmap数据访问对象
"""

import unittest
from unittest.mock import MagicMock, patch

from src.roadmap.dao.roadmap_dao import RoadmapDAO


class TestRoadmapDAO(unittest.TestCase):
    """测试Roadmap数据访问对象"""

    def setUp(self):
        """设置测试环境"""
        # 创建DAO实例
        self.dao = RoadmapDAO()

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_get_roadmap(self, mock_get_session):
        """测试获取路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = "roadmap1"
        mock_roadmap.name = "测试路线图"
        mock_roadmap.description = "测试描述"
        mock_roadmap.to_dict.return_value = {"id": "roadmap1", "name": "测试路线图", "description": "测试描述"}

        # 配置session查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_roadmap
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试获取路线图
        roadmap = self.dao.get_roadmap("roadmap1")

        # 验证调用
        mock_session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        self.assertEqual(roadmap["id"], "roadmap1")
        self.assertEqual(roadmap["name"], "测试路线图")

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_get_roadmap_not_found(self, mock_get_session):
        """测试获取不存在的路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        # 配置session查询结果为None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试获取不存在的路线图
        roadmap = self.dao.get_roadmap("nonexistent")

        # 验证结果为None
        self.assertIsNone(roadmap)

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_get_all_roadmaps(self, mock_get_session):
        """测试获取所有路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_roadmap1 = MagicMock()
        mock_roadmap1.to_dict.return_value = {"id": "roadmap1", "name": "路线图1"}
        mock_roadmap2 = MagicMock()
        mock_roadmap2.to_dict.return_value = {"id": "roadmap2", "name": "路线图2"}

        # 配置session查询结果
        mock_query = MagicMock()
        mock_query.all.return_value = [mock_roadmap1, mock_roadmap2]
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试获取所有路线图
        roadmaps = self.dao.get_all_roadmaps()

        # 验证调用
        mock_session.query.assert_called_once()
        mock_query.all.assert_called_once()
        self.assertEqual(len(roadmaps), 2)
        self.assertEqual(roadmaps[0]["id"], "roadmap1")
        self.assertEqual(roadmaps[1]["id"], "roadmap2")

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    @patch("src.roadmap.dao.roadmap_dao.Roadmap")
    @patch("src.roadmap.dao.roadmap_dao.uuid.uuid4")
    def test_create_roadmap(self, mock_uuid, mock_roadmap_class, mock_get_session):
        """测试创建路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.hex = "new-roadmap-id"

        # 模拟Roadmap实例
        mock_roadmap = MagicMock()
        mock_roadmap.id = "new-roadmap-id"
        mock_roadmap.name = "新路线图"
        mock_roadmap.description = "新描述"
        mock_roadmap.to_dict.return_value = {"id": "new-roadmap-id", "name": "新路线图", "description": "新描述"}
        mock_roadmap_class.return_value = mock_roadmap

        # 配置session
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试创建路线图
        roadmap_data = {"name": "新路线图", "description": "新描述"}
        result = self.dao.create_roadmap(roadmap_data)

        # 验证调用
        mock_roadmap_class.assert_called_once()
        mock_session.add.assert_called_once_with(mock_roadmap)
        mock_session.commit.assert_called_once()
        self.assertEqual(result["id"], "new-roadmap-id")
        self.assertEqual(result["name"], "新路线图")

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_update_roadmap(self, mock_get_session):
        """测试更新路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = "roadmap1"
        mock_roadmap.name = "旧路线图"
        mock_roadmap.description = "旧描述"
        mock_roadmap.to_dict.return_value = {"id": "roadmap1", "name": "更新的路线图", "description": "更新的描述"}

        # 配置session查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_roadmap
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试更新路线图
        roadmap_data = {"name": "更新的路线图", "description": "更新的描述"}
        result = self.dao.update_roadmap("roadmap1", roadmap_data)

        # 验证调用
        mock_session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        self.assertEqual(mock_roadmap.name, "更新的路线图")
        self.assertEqual(mock_roadmap.description, "更新的描述")
        mock_session.commit.assert_called_once()
        self.assertEqual(result["id"], "roadmap1")
        self.assertEqual(result["name"], "更新的路线图")

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_update_roadmap_not_found(self, mock_get_session):
        """测试更新不存在的路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        # 配置session查询结果为None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试更新不存在的路线图
        roadmap_data = {"name": "更新的路线图"}
        result = self.dao.update_roadmap("nonexistent", roadmap_data)

        # 验证结果为None
        self.assertIsNone(result)

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_delete_roadmap(self, mock_get_session):
        """测试删除路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = "roadmap1"

        # 配置session查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_roadmap
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试删除路线图
        result = self.dao.delete_roadmap("roadmap1")

        # 验证调用
        mock_session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_session.delete.assert_called_once_with(mock_roadmap)
        mock_session.commit.assert_called_once()
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], "roadmap1")

    @patch("src.roadmap.dao.roadmap_dao.get_session_factory")
    def test_delete_roadmap_not_found(self, mock_get_session):
        """测试删除不存在的路线图"""
        # 设置模拟对象
        mock_session = MagicMock()
        # 配置session查询结果为None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__enter__.return_value = mock_session
        mock_get_session.return_value = mock_session_factory

        # 测试删除不存在的路线图
        result = self.dao.delete_roadmap("nonexistent")

        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Roadmap not found")


if __name__ == "__main__":
    unittest.main()
