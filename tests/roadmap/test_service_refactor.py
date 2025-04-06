"""
重构后的路线图服务测试模块

测试重构后的路线图服务及其相关组件的功能和集成
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import Session

from src.roadmap.service.roadmap_service import RoadmapService


class TestRoadmapServiceRefactor(unittest.TestCase):
    """测试重构后的路线图服务"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟会话
        self.mock_session = MagicMock(spec=Session)

        # 创建服务实例
        self.service = RoadmapService(session=self.mock_session)

    def test_service_initialization(self):
        """测试服务初始化"""
        # 验证核心组件已初始化
        self.assertIsNotNone(self.service.manager)
        self.assertIsNotNone(self.service.status)
        self.assertIsNotNone(self.service.updater)

        # 验证同步服务已初始化
        self.assertIsNotNone(self.service.github_sync)
        self.assertIsNotNone(self.service.yaml_sync)

        # 验证仓库已初始化
        self.assertIsNotNone(self.service.epic_repo)
        self.assertIsNotNone(self.service.story_repo)
        self.assertIsNotNone(self.service.task_repo)

    def test_create_roadmap(self):
        """测试创建路线图"""
        # 创建路线图
        result = self.service.create_roadmap("测试路线图", "这是一个测试路线图")

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_name"], "测试路线图")
        self.assertIsNotNone(result["roadmap_id"])

        # 验证活跃路线图已设置
        self.assertEqual(self.service.active_roadmap_id, result["roadmap_id"])

    def test_switch_roadmap(self):
        """测试切换路线图"""
        # 创建两个路线图
        result1 = self.service.create_roadmap("路线图1")
        result2 = self.service.create_roadmap("路线图2")

        # 切换到第一个路线图
        switch_result = self.service.switch_roadmap(result1["roadmap_id"])

        # 验证结果
        self.assertTrue(switch_result["success"])
        self.assertEqual(switch_result["roadmap_id"], result1["roadmap_id"])
        self.assertEqual(self.service.active_roadmap_id, result1["roadmap_id"])

    def test_list_roadmaps(self):
        """测试获取路线图列表"""
        # 创建路线图
        self.service.create_roadmap("路线图1")
        self.service.create_roadmap("路线图2")

        # 获取路线图列表
        result = self.service.list_roadmaps()

        # 验证结果
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["active_id"])
        self.assertGreaterEqual(len(result["roadmaps"]), 2)

    def test_get_roadmap_info(self):
        """测试获取路线图信息"""
        # 创建路线图
        create_result = self.service.create_roadmap("测试路线图")
        roadmap_id = create_result["roadmap_id"]

        # 获取路线图信息
        result = self.service.get_roadmap_info(roadmap_id)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap"]["id"], roadmap_id)
        self.assertIn("stats", result)
        self.assertIn("status", result)

    def test_update_roadmap_status(self):
        """测试更新路线图状态"""
        # 创建路线图
        create_result = self.service.create_roadmap("测试路线图")
        roadmap_id = create_result["roadmap_id"]

        # 获取里程碑
        milestones = self.service.get_milestones(roadmap_id)
        self.assertGreater(len(milestones), 0)

        # 更新里程碑状态
        milestone_id = milestones[0]["id"]
        result = self.service.update_roadmap_status(milestone_id, "milestone", "in_progress")

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["element"]["id"], milestone_id)
        self.assertEqual(result["element"]["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
