"""
路线图状态测试模块

测试路线图状态管理功能。
"""

import unittest
from unittest.mock import MagicMock

from src.db.service import DatabaseService
from src.roadmap.core.status import RoadmapStatus


class TestRoadmapStatus(unittest.TestCase):
    """路线图状态测试"""

    def setUp(self):
        """测试准备"""
        # 模拟依赖服务
        self.db_service = MagicMock(spec=DatabaseService)

        # 设置活跃路线图
        self.db_service.active_roadmap_id = "roadmap-123"

        # 创建状态实例
        self.status = RoadmapStatus(self.db_service)

    def test_update_milestone_query(self):
        """测试查询里程碑状态"""
        # 模拟依赖服务返回值
        milestone_id = "milestone-1"
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
            "progress": 50,
        }

        # 执行测试
        result = self.status.update_element(milestone_id, "milestone")

        # 验证结果
        self.assertEqual(result["id"], milestone_id)
        self.assertEqual(result["name"], "里程碑1")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["progress"], 50)
        self.assertFalse(result["updated"])

        # 验证依赖调用
        self.db_service.get_milestone.assert_called_once_with(milestone_id, "roadmap-123")
        self.db_service.update_milestone.assert_not_called()

    def test_update_milestone_status(self):
        """测试更新里程碑状态"""
        # 模拟依赖服务返回值
        milestone_id = "milestone-1"
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
            "progress": 50,
        }

        # 执行测试
        result = self.status.update_element(milestone_id, "milestone", "completed")

        # 验证结果
        self.assertEqual(result["id"], milestone_id)
        self.assertEqual(result["name"], "里程碑1")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertTrue(result["updated"])

        # 验证依赖调用
        self.db_service.get_milestone.assert_called_once_with(milestone_id, "roadmap-123")
        self.db_service.update_milestone.assert_called_once()
        update_call = self.db_service.update_milestone.call_args[0]
        self.assertEqual(update_call[0], milestone_id)
        self.assertEqual(update_call[1]["status"], "completed")
        self.assertEqual(update_call[1]["progress"], 100)

    def test_update_milestone_invalid_status(self):
        """测试更新里程碑无效状态"""
        # 模拟依赖服务返回值
        milestone_id = "milestone-1"
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
            "progress": 50,
        }

        # 执行测试
        result = self.status.update_element(milestone_id, "milestone", "invalid")

        # 验证结果
        self.assertFalse(result["updated"])
        self.assertIn("error", result)
        self.assertIn("无效的里程碑状态", result["error"])

        # 验证依赖调用
        self.db_service.update_milestone.assert_not_called()

    def test_update_task_query(self):
        """测试查询任务状态"""
        # 模拟依赖服务返回值
        task_id = "task-1"
        self.db_service.get_task.return_value = {
            "id": task_id,
            "title": "任务1",
            "status": "in_progress",
            "milestone": "milestone-1",
        }

        # 执行测试
        result = self.status.update_element(task_id, "task")

        # 验证结果
        self.assertEqual(result["id"], task_id)
        self.assertEqual(result["title"], "任务1")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["milestone"], "milestone-1")
        self.assertFalse(result["updated"])

        # 验证依赖调用
        self.db_service.get_task.assert_called_once_with(task_id, "roadmap-123")

    def test_update_task_status(self):
        """测试更新任务状态"""
        # 模拟依赖服务返回值
        task_id = "task-1"
        self.db_service.get_task.return_value = {
            "id": task_id,
            "title": "任务1",
            "status": "in_progress",
            "milestone": "milestone-1",
        }

        # 执行测试
        result = self.status.update_element(task_id, "task", "completed")

        # 验证结果
        self.assertEqual(result["id"], task_id)
        self.assertEqual(result["title"], "任务1")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["milestone"], "milestone-1")
        self.assertTrue(result["updated"])

    def test_update_invalid_element_type(self):
        """测试更新无效元素类型"""
        # 执行测试
        result = self.status.update_element("id-1", "invalid")

        # 验证结果
        self.assertFalse(result["updated"])
        self.assertIn("error", result)
        self.assertIn("不支持的元素类型", result["error"])


if __name__ == "__main__":
    unittest.main()
