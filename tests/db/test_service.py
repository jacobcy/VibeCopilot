"""
数据库服务测试模块

测试DatabaseService类提供的各种数据库操作功能
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.db.service import DatabaseService


class TestDatabaseService(unittest.TestCase):
    """数据库服务测试类"""

    def setUp(self):
        """测试准备"""
        # 创建测试实例
        self.patch_init_db = patch("src.db.service.init_db")
        self.mock_init_db = self.patch_init_db.start()

        self.patch_session_factory = patch("src.db.service.get_session_factory")
        self.mock_session_factory = self.patch_session_factory.start()

        # 设置模拟会话
        self.mock_session = MagicMock()
        self.mock_session_factory.return_value.return_value = self.mock_session

        # 模拟仓库
        self.mock_epic_repo = MagicMock()
        self.mock_story_repo = MagicMock()
        self.mock_task_repo = MagicMock()

        # 模拟实体管理器和特定管理器
        self.mock_entity_manager = MagicMock()
        self.mock_epic_manager = MagicMock()
        self.mock_story_manager = MagicMock()
        self.mock_task_manager = MagicMock()

        # 创建服务实例
        with patch("src.db.service.EpicRepository", return_value=self.mock_epic_repo), patch(
            "src.db.service.StoryRepository", return_value=self.mock_story_repo
        ), patch("src.db.service.TaskRepository", return_value=self.mock_task_repo), patch(
            "src.db.service.EntityManager", return_value=self.mock_entity_manager
        ), patch(
            "src.db.service.EpicManager", return_value=self.mock_epic_manager
        ), patch(
            "src.db.service.StoryManager", return_value=self.mock_story_manager
        ), patch(
            "src.db.service.TaskManager", return_value=self.mock_task_manager
        ):
            self.db_service = DatabaseService()

    def tearDown(self):
        """测试清理"""
        self.patch_init_db.stop()
        self.patch_session_factory.stop()

    def test_epic_crud(self):
        """测试Epic的CRUD操作"""
        # 准备测试数据
        epic_data = {"title": "测试Epic", "description": "Epic描述"}
        epic_id = "epic_12345678"
        mock_epic = {"id": epic_id, "title": "测试Epic", "description": "Epic描述"}

        # 模拟管理器方法的返回值
        self.mock_epic_manager.create_epic.return_value = mock_epic
        self.mock_epic_manager.get_epic.return_value = mock_epic
        self.mock_epic_manager.update_epic.return_value = {**mock_epic, "status": "in_progress"}
        self.mock_epic_manager.delete_epic.return_value = True
        self.mock_epic_manager.list_epics.return_value = [mock_epic]

        # 测试创建
        result = self.db_service.create_epic(epic_data)
        self.mock_epic_manager.create_epic.assert_called_once_with(epic_data)
        self.assertEqual(result, mock_epic)

        # 测试获取
        result = self.db_service.get_epic(epic_id)
        self.mock_epic_manager.get_epic.assert_called_once_with(epic_id)
        self.assertEqual(result, mock_epic)

        # 测试更新
        update_data = {"status": "in_progress"}
        result = self.db_service.update_epic(epic_id, update_data)
        self.mock_epic_manager.update_epic.assert_called_once_with(epic_id, update_data)
        self.assertEqual(result["status"], "in_progress")

        # 测试删除
        result = self.db_service.delete_epic(epic_id)
        self.mock_epic_manager.delete_epic.assert_called_once_with(epic_id)
        self.assertTrue(result)

        # 测试列表
        result = self.db_service.list_epics()
        self.mock_epic_manager.list_epics.assert_called_once()
        self.assertEqual(result, [mock_epic])

    def test_story_crud(self):
        """测试Story的CRUD操作"""
        # 准备测试数据
        story_data = {"title": "测试Story", "description": "Story描述", "epic_id": "epic_12345678"}
        story_id = "story_12345678"
        mock_story = {"id": story_id, "title": "测试Story", "description": "Story描述", "epic_id": "epic_12345678"}

        # 模拟管理器方法的返回值
        self.mock_story_manager.create_story.return_value = mock_story
        self.mock_story_manager.get_story.return_value = mock_story
        self.mock_story_manager.update_story.return_value = {**mock_story, "status": "in_progress"}
        self.mock_story_manager.delete_story.return_value = True
        self.mock_story_manager.list_stories.return_value = [mock_story]

        # 测试创建
        result = self.db_service.create_story(story_data)
        self.mock_story_manager.create_story.assert_called_once_with(story_data)
        self.assertEqual(result, mock_story)

        # 测试获取
        result = self.db_service.get_story(story_id)
        self.mock_story_manager.get_story.assert_called_once_with(story_id)
        self.assertEqual(result, mock_story)

        # 测试更新
        update_data = {"status": "in_progress"}
        result = self.db_service.update_story(story_id, update_data)
        self.mock_story_manager.update_story.assert_called_once_with(story_id, update_data)
        self.assertEqual(result["status"], "in_progress")

        # 测试删除
        result = self.db_service.delete_story(story_id)
        self.mock_story_manager.delete_story.assert_called_once_with(story_id)
        self.assertTrue(result)

        # 测试列表
        result = self.db_service.list_stories()
        self.mock_story_manager.list_stories.assert_called_once()
        self.assertEqual(result, [mock_story])

    def test_task_crud(self):
        """测试Task的CRUD操作"""
        # 准备测试数据
        task_data = {"title": "测试Task", "description": "Task描述", "story_id": "story_12345678"}
        task_id = "task_12345678"
        mock_task = {"id": task_id, "title": "测试Task", "description": "Task描述", "story_id": "story_12345678", "status": "todo"}

        # 模拟管理器方法的返回值
        self.mock_task_manager.create_task.return_value = mock_task
        self.mock_task_manager.get_task.return_value = mock_task
        self.mock_task_manager.update_task.return_value = {**mock_task, "status": "in_progress"}
        self.mock_task_manager.delete_task.return_value = True
        self.mock_task_manager.list_tasks.return_value = [mock_task]

        # 测试创建
        result = self.db_service.create_task(task_data)
        self.mock_task_manager.create_task.assert_called_once_with(task_data)
        self.assertEqual(result, mock_task)

        # 测试获取
        result = self.db_service.get_task(task_id)
        self.mock_task_manager.get_task.assert_called_once_with(task_id)
        self.assertEqual(result, mock_task)

        # 测试更新
        update_data = {"status": "in_progress"}
        result = self.db_service.update_task(task_id, update_data)
        self.mock_task_manager.update_task.assert_called_once_with(task_id, update_data)
        self.assertEqual(result["status"], "in_progress")

        # 测试删除
        result = self.db_service.delete_task(task_id)
        self.mock_task_manager.delete_task.assert_called_once_with(task_id)
        self.assertTrue(result)

        # 测试列表
        result = self.db_service.list_tasks()
        self.mock_task_manager.list_tasks.assert_called_once()
        self.assertEqual(result, [mock_task])

    def test_generic_entity_operations(self):
        """测试通用实体操作方法"""
        # 模拟EntityManager的返回值
        self.mock_entity_manager.get_entity.return_value = {"id": "test_1", "name": "测试"}
        self.mock_entity_manager.get_entities.return_value = [{"id": "test_1", "name": "测试"}]
        self.mock_entity_manager.create_entity.return_value = {"id": "test_2", "name": "新测试"}
        self.mock_entity_manager.update_entity.return_value = {"id": "test_1", "name": "更新测试"}
        self.mock_entity_manager.delete_entity.return_value = True
        self.mock_entity_manager.search_entities.return_value = [{"id": "test_1", "name": "测试"}]

        # 测试获取实体
        result = self.db_service.get_entity("test", "test_1")
        self.mock_entity_manager.get_entity.assert_called_once_with("test", "test_1")
        self.assertEqual(result["id"], "test_1")

        # 测试获取实体列表
        result = self.db_service.get_entities("test")
        self.mock_entity_manager.get_entities.assert_called_once_with("test")
        self.assertEqual(len(result), 1)

        # 测试创建实体
        data = {"name": "新测试"}
        result = self.db_service.create_entity("test", data)
        self.mock_entity_manager.create_entity.assert_called_once_with("test", data)
        self.assertEqual(result["name"], "新测试")

        # 测试更新实体
        data = {"name": "更新测试"}
        result = self.db_service.update_entity("test", "test_1", data)
        self.mock_entity_manager.update_entity.assert_called_once_with("test", "test_1", data)
        self.assertEqual(result["name"], "更新测试")

        # 测试删除实体
        result = self.db_service.delete_entity("test", "test_1")
        self.mock_entity_manager.delete_entity.assert_called_once_with("test", "test_1")
        self.assertTrue(result)

        # 测试搜索实体
        result = self.db_service.search_entities("test", "测试")
        self.mock_entity_manager.search_entities.assert_called_once_with("test", "测试")
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
