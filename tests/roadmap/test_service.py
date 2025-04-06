"""
路线图服务测试模块

测试路线图服务功能。
"""

import unittest
from unittest.mock import MagicMock, patch

from src.db.service import DatabaseService
from src.db.sync import DataSynchronizer
from src.roadmap.service.roadmap_service import RoadmapService


class TestRoadmapService(unittest.TestCase):
    """路线图服务测试"""

    def setUp(self):
        """测试准备"""
        # 模拟依赖服务
        self.db_service = MagicMock(spec=DatabaseService)
        self.data_sync = MagicMock(spec=DataSynchronizer)

        # 设置活跃路线图
        self.db_service.active_roadmap_id = "roadmap-123"

        # 创建服务实例
        self.service = RoadmapService(self.db_service, self.data_sync)

        # 模拟核心组件
        self.service.manager = MagicMock()
        self.service.status = MagicMock()
        self.service.updater = MagicMock()
        self.service.github_sync = MagicMock()
        self.service.yaml_sync = MagicMock()

    def test_create_roadmap(self):
        """测试创建路线图"""
        # 模拟依赖服务返回值
        self.db_service.create_roadmap.return_value = "roadmap-new"

        # 执行测试
        result = self.service.create_roadmap("测试路线图", "测试描述", "1.0")

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], "roadmap-new")
        self.assertEqual(result["roadmap_name"], "测试路线图")

        # 验证依赖调用
        self.db_service.create_roadmap.assert_called_once()
        roadmap_data = self.db_service.create_roadmap.call_args[0][0]
        self.assertEqual(roadmap_data["name"], "测试路线图")
        self.assertEqual(roadmap_data["description"], "测试描述")
        self.assertEqual(roadmap_data["version"], "1.0")

    def test_switch_roadmap(self):
        """测试切换路线图"""
        # 模拟依赖服务返回值
        roadmap_id = "roadmap-456"
        self.db_service.get_roadmap.return_value = {"id": roadmap_id, "name": "路线图2"}

        # 执行测试
        result = self.service.switch_roadmap(roadmap_id)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], roadmap_id)
        self.assertEqual(result["roadmap_name"], "路线图2")

        # 验证依赖调用
        self.db_service.get_roadmap.assert_called_once_with(roadmap_id)
        self.db_service.set_active_roadmap.assert_called_once_with(roadmap_id)

    def test_switch_roadmap_not_found(self):
        """测试切换不存在的路线图"""
        # 模拟依赖服务返回值
        roadmap_id = "roadmap-invalid"
        self.db_service.get_roadmap.return_value = None

        # 执行测试
        result = self.service.switch_roadmap(roadmap_id)

        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("未找到路线图", result["error"])

        # 验证依赖调用
        self.db_service.get_roadmap.assert_called_once_with(roadmap_id)
        self.db_service.set_active_roadmap.assert_not_called()

    def test_list_roadmaps(self):
        """测试列出所有路线图"""
        # 模拟依赖服务返回值
        self.db_service.get_roadmaps.return_value = [
            {"id": "roadmap-123", "name": "路线图1"},
            {"id": "roadmap-456", "name": "路线图2"},
        ]

        # 执行测试
        result = self.service.list_roadmaps()

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["active_id"], "roadmap-123")
        self.assertEqual(len(result["roadmaps"]), 2)

        # 验证依赖调用
        self.db_service.get_roadmaps.assert_called_once()

    def test_delete_roadmap(self):
        """测试删除路线图"""
        # 模拟依赖服务返回值
        roadmap_id = "roadmap-456"
        self.db_service.get_roadmap.return_value = {"id": roadmap_id, "name": "路线图2"}

        # 执行测试
        result = self.service.delete_roadmap(roadmap_id)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap_id"], roadmap_id)
        self.assertEqual(result["roadmap_name"], "路线图2")

        # 验证依赖调用
        self.db_service.get_roadmap.assert_called_once_with(roadmap_id)
        self.db_service.delete_roadmap.assert_called_once_with(roadmap_id)

    def test_delete_active_roadmap(self):
        """测试删除活跃路线图"""
        # 模拟依赖服务返回值
        roadmap_id = "roadmap-123"  # 与活跃路线图ID相同
        self.db_service.get_roadmap.return_value = {"id": roadmap_id, "name": "路线图1"}

        # 执行测试
        result = self.service.delete_roadmap(roadmap_id)

        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("不能删除当前活跃路线图", result["error"])

        # 验证依赖调用
        self.db_service.delete_roadmap.assert_not_called()

    def test_get_roadmap_info(self):
        """测试获取路线图信息"""
        # 模拟依赖服务返回值
        roadmap_id = "roadmap-123"
        self.db_service.get_roadmap.return_value = {"id": roadmap_id, "name": "路线图1"}
        self.db_service.get_epics.return_value = [{"id": "epic-1"}, {"id": "epic-2"}]
        self.db_service.get_milestones.return_value = [{"id": "milestone-1"}, {"id": "milestone-2"}]
        self.db_service.get_stories.return_value = [
            {"id": "story-1"},
            {"id": "story-2"},
            {"id": "story-3"},
        ]
        self.db_service.get_milestone_tasks.return_value = [
            {"id": "task-1", "status": "completed"},
            {"id": "task-2", "status": "in_progress"},
        ]
        self.service.manager.check_roadmap.return_value = {"status": "on_track"}

        # 执行测试
        result = self.service.get_roadmap_info(roadmap_id)

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["roadmap"], {"id": roadmap_id, "name": "路线图1"})
        self.assertEqual(result["stats"]["epics_count"], 2)
        self.assertEqual(result["stats"]["milestones_count"], 2)
        self.assertEqual(result["stats"]["stories_count"], 3)
        self.assertEqual(result["stats"]["tasks_count"], 4)  # 2任务/里程碑 × 2里程碑
        self.assertEqual(result["stats"]["completed_tasks"], 2)  # 1完成/里程碑 × 2里程碑
        self.assertEqual(result["stats"]["progress"], 50)  # 2/4 = 50%

        # 验证依赖调用
        self.db_service.get_roadmap.assert_called_once_with(roadmap_id)
        self.db_service.get_epics.assert_called_once_with(roadmap_id)
        self.db_service.get_milestones.assert_called_once_with(roadmap_id)
        self.db_service.get_stories.assert_called_once_with(roadmap_id)
        self.assertEqual(self.db_service.get_milestone_tasks.call_count, 2)
        self.service.manager.check_roadmap.assert_called_once_with("roadmap", roadmap_id=roadmap_id)

    def test_update_roadmap_status(self):
        """测试更新路线图元素状态"""
        # 模拟依赖服务返回值
        element_id = "task-1"
        self.service.status.update_element.return_value = {
            "id": element_id,
            "title": "任务1",
            "status": "completed",
            "updated": True,
        }

        # 执行测试
        result = self.service.update_roadmap_status(element_id, "task", "completed")

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["element"]["id"], element_id)
        self.assertEqual(result["element"]["status"], "completed")

        # 验证依赖调用
        self.service.status.update_element.assert_called_once_with(
            element_id, "task", "completed", "roadmap-123"
        )

    def test_check_roadmap_status(self):
        """测试检查路线图状态"""
        # 模拟依赖服务返回值
        self.service.manager.check_roadmap.return_value = {
            "milestones": 2,
            "tasks": 5,
            "task_status": {"todo": 2, "in_progress": 1, "completed": 2},
        }

        # 执行测试
        result = self.service.check_roadmap_status("entire")

        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["check_type"], "entire")
        self.assertEqual(result["roadmap_id"], "roadmap-123")
        self.assertEqual(result["status"]["milestones"], 2)
        self.assertEqual(result["status"]["tasks"], 5)

        # 验证依赖调用
        self.service.manager.check_roadmap.assert_called_once_with("entire", None, "roadmap-123")

    def test_update_roadmap(self):
        """测试更新路线图数据"""
        # 模拟依赖服务返回值
        self.service.updater.update_roadmap.return_value = {
            "success": True,
            "roadmap_id": "roadmap-123",
            "file_path": "/path/to/roadmap.yaml",
        }

        # 执行测试
        result = self.service.update_roadmap()

        # 验证结果
        self.assertEqual(result["success"], True)
        self.assertEqual(result["roadmap_id"], "roadmap-123")

        # 验证依赖调用
        self.service.updater.update_roadmap.assert_called_once_with("roadmap-123")

    def test_sync_to_github(self):
        """测试同步到GitHub"""
        # 模拟依赖服务返回值
        self.service.github_sync.sync_roadmap_to_github.return_value = {
            "success": True,
            "roadmap_id": "roadmap-123",
        }

        # 执行测试
        result = self.service.sync_to_github()

        # 验证结果
        self.assertEqual(result["success"], True)
        self.assertEqual(result["roadmap_id"], "roadmap-123")

        # 验证依赖调用
        self.service.github_sync.sync_roadmap_to_github.assert_called_once_with("roadmap-123")

    def test_sync_from_github(self):
        """测试从GitHub同步"""
        # 模拟依赖服务返回值
        self.service.github_sync.sync_status_from_github.return_value = {
            "success": True,
            "roadmap_id": "roadmap-123",
        }

        # 执行测试
        result = self.service.sync_from_github()

        # 验证结果
        self.assertEqual(result["success"], True)
        self.assertEqual(result["roadmap_id"], "roadmap-123")

        # 验证依赖调用
        self.service.github_sync.sync_status_from_github.assert_called_once_with("roadmap-123")

    def test_export_to_yaml(self):
        """测试导出到YAML"""
        # 模拟依赖服务返回值
        self.service.yaml_sync.export_to_yaml.return_value = {
            "success": True,
            "roadmap_id": "roadmap-123",
            "file_path": "/path/to/roadmap.yaml",
        }

        # 执行测试
        result = self.service.export_to_yaml()

        # 验证结果
        self.assertEqual(result["success"], True)
        self.assertEqual(result["roadmap_id"], "roadmap-123")
        self.assertEqual(result["file_path"], "/path/to/roadmap.yaml")

        # 验证依赖调用
        self.service.yaml_sync.export_to_yaml.assert_called_once_with("roadmap-123", None)

    def test_import_from_yaml(self):
        """测试从YAML导入"""
        # 模拟依赖服务返回值
        file_path = "/path/to/roadmap.yaml"
        self.service.yaml_sync.import_from_yaml.return_value = {
            "success": True,
            "roadmap_id": "roadmap-new",
            "source_file": file_path,
        }

        # 执行测试
        result = self.service.import_from_yaml(file_path)

        # 验证结果
        self.assertEqual(result["success"], True)
        self.assertEqual(result["roadmap_id"], "roadmap-new")
        self.assertEqual(result["source_file"], file_path)

        # 验证依赖调用
        self.service.yaml_sync.import_from_yaml.assert_called_once_with(file_path, None)


if __name__ == "__main__":
    unittest.main()
