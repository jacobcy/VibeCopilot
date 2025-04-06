"""
路线图管理器测试模块

测试路线图核心管理功能。
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.db.service import DatabaseService
from src.db.sync import DataSynchronizer
from src.roadmap.core.manager import RoadmapManager


class TestRoadmapManager(unittest.TestCase):
    """路线图管理器测试"""

    def setUp(self):
        """测试准备"""
        # 模拟依赖服务
        self.db_service = MagicMock(spec=DatabaseService)
        self.data_sync = MagicMock(spec=DataSynchronizer)

        # 设置环境变量
        self.original_project_root = os.environ.get("PROJECT_ROOT")
        os.environ["PROJECT_ROOT"] = "/tmp/vibecopilot_test"

        # 创建测试目录
        os.makedirs("/tmp/vibecopilot_test/.ai/roadmap", exist_ok=True)

        # 设置活跃路线图
        self.db_service.active_roadmap_id = "roadmap-123"

        # 创建管理器实例
        self.manager = RoadmapManager(self.db_service, self.data_sync)

    def tearDown(self):
        """测试清理"""
        # 恢复环境变量
        if self.original_project_root:
            os.environ["PROJECT_ROOT"] = self.original_project_root
        else:
            os.environ.pop("PROJECT_ROOT", None)

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.manager.db_service, self.db_service)
        self.assertEqual(self.manager.data_sync, self.data_sync)
        self.assertEqual(self.manager.roadmap_dir, "/tmp/vibecopilot_test/.ai/roadmap")

    def test_check_entire_roadmap(self):
        """测试检查整个路线图"""
        # 模拟依赖服务返回值
        self.db_service.get_milestones.return_value = [
            {"id": "milestone-1", "name": "里程碑1", "status": "in_progress", "progress": 50},
            {"id": "milestone-2", "name": "里程碑2", "status": "planned", "progress": 0},
        ]
        self.db_service.list_tasks.return_value = [
            {"id": "task-1", "title": "任务1", "status": "todo", "milestone": "milestone-1"},
            {"id": "task-2", "title": "任务2", "status": "in_progress", "milestone": "milestone-1"},
            {"id": "task-3", "title": "任务3", "status": "completed", "milestone": "milestone-2"},
        ]

        # 执行测试
        result = self.manager.check_roadmap("roadmap")

        # 验证结果
        self.assertEqual(result["milestones"], 2)
        self.assertEqual(result["tasks"], 3)
        self.assertEqual(result["active_milestone"], "milestone-1")
        self.assertEqual(result["task_status"]["todo"], 1)
        self.assertEqual(result["task_status"]["in_progress"], 1)
        self.assertEqual(result["task_status"]["completed"], 1)

        # 验证依赖调用
        self.db_service.get_milestones.assert_called_once_with("roadmap-123")
        self.db_service.list_tasks.assert_called_once_with("roadmap-123")

    def test_check_milestone(self):
        """测试检查里程碑"""
        # 模拟依赖服务返回值
        milestone_id = "milestone-1"
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
            "progress": 50,
        }
        self.db_service.list_tasks.return_value = [
            {"id": "task-1", "title": "任务1", "status": "todo", "milestone": milestone_id},
            {"id": "task-2", "title": "任务2", "status": "in_progress", "milestone": milestone_id},
            {"id": "task-3", "title": "任务3", "status": "completed", "milestone": milestone_id},
        ]

        # 执行测试
        result = self.manager.check_roadmap("milestone", milestone_id)

        # 验证结果
        self.assertEqual(result["milestone_id"], milestone_id)
        self.assertEqual(result["name"], "里程碑1")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["progress"], 33)  # 1/3完成 = 33%
        self.assertEqual(result["tasks"], 3)
        self.assertEqual(result["task_status"]["todo"], 1)
        self.assertEqual(result["task_status"]["in_progress"], 1)
        self.assertEqual(result["task_status"]["completed"], 1)

        # 验证依赖调用
        self.db_service.get_milestone.assert_called_once_with(milestone_id, "roadmap-123")
        self.db_service.list_tasks.assert_called_once_with("roadmap-123")

    def test_check_milestone_with_update(self):
        """测试检查并更新里程碑"""
        # 模拟依赖服务返回值
        milestone_id = "milestone-1"
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
            "progress": 50,
        }
        self.db_service.list_tasks.return_value = [
            {"id": "task-1", "title": "任务1", "status": "completed", "milestone": milestone_id},
            {"id": "task-2", "title": "任务2", "status": "completed", "milestone": milestone_id},
        ]

        # 执行测试
        result = self.manager.check_roadmap("milestone", milestone_id, update=True)

        # 验证结果
        self.assertEqual(result["progress"], 100)  # 全部完成 = 100%

        # 验证更新调用
        self.db_service.update_milestone.assert_called_once()
        update_call = self.db_service.update_milestone.call_args[0]
        self.assertEqual(update_call[0], milestone_id)
        self.assertEqual(update_call[1]["progress"], 100)
        self.assertEqual(update_call[1]["status"], "completed")

    def test_check_task(self):
        """测试检查任务"""
        # 模拟依赖服务返回值
        task_id = "task-1"
        milestone_id = "milestone-1"
        self.db_service.get_task.return_value = {
            "id": task_id,
            "title": "任务1",
            "status": "in_progress",
            "priority": "high",
            "milestone": milestone_id,
        }
        self.db_service.get_milestone.return_value = {
            "id": milestone_id,
            "name": "里程碑1",
            "status": "in_progress",
        }

        # 执行测试
        result = self.manager.check_roadmap("task", task_id)

        # 验证结果
        self.assertEqual(result["task_id"], task_id)
        self.assertEqual(result["title"], "任务1")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["milestone"]["id"], milestone_id)
        self.assertEqual(result["milestone"]["name"], "里程碑1")
        self.assertEqual(result["milestone"]["status"], "in_progress")

        # 验证依赖调用
        self.db_service.get_task.assert_called_once_with(task_id, "roadmap-123")
        self.db_service.get_milestone.assert_called_once_with(milestone_id, "roadmap-123")

    def test_check_roadmap_invalid_type(self):
        """测试无效的检查类型"""
        with self.assertRaises(ValueError):
            self.manager.check_roadmap("invalid")

    def test_check_milestone_missing_id(self):
        """测试检查里程碑但未提供ID"""
        with self.assertRaises(ValueError):
            self.manager.check_roadmap("milestone")

    def test_check_task_missing_id(self):
        """测试检查任务但未提供ID"""
        with self.assertRaises(ValueError):
            self.manager.check_roadmap("task")


if __name__ == "__main__":
    unittest.main()
