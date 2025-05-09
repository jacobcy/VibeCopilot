#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试隐式Story创建和关联功能
"""

import unittest
from unittest.mock import MagicMock, call, patch

from src.roadmap.service import RoadmapService
from src.sync.importers.milestone_importer import MilestoneImporter


class TestImplicitStory(unittest.TestCase):
    """测试隐式Story创建和关联功能"""

    def setUp(self):
        """测试前设置"""
        self.mock_session = MagicMock()
        self.mock_roadmap_service = MagicMock()

        # 配置roadmap_service的共享方法
        self.mock_roadmap_service.get_now.return_value = "2023-01-01T00:00:00"
        self.mock_story_repo = MagicMock()
        self.mock_epic_repo = MagicMock()
        self.mock_roadmap_service.story_repo = self.mock_story_repo
        self.mock_roadmap_service.epic_repo = self.mock_epic_repo

    @patch("src.sync.importers.milestone_importer.session_scope")
    def test_milestone_importer_creates_implicit_story(self, mock_session_scope):
        """测试里程碑导入器创建隐式Story"""
        # 配置session_scope的模拟
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = self.mock_session
        mock_session_scope.return_value = mock_session_context

        # 配置RoadmapService.get_or_create_implicit_story_for_milestone的行为
        self.mock_roadmap_service.get_or_create_implicit_story_for_milestone.return_value = "story-123"

        # 配置TaskImporter依赖项
        mock_task_importer = MagicMock()

        # 创建MilestoneImporter实例并注入依赖
        with patch("src.sync.importers.milestone_importer.TaskImporter", return_value=mock_task_importer):
            importer = MilestoneImporter(self.mock_roadmap_service, verbose=True, stop_on_error=False)

            # 模拟数据
            yaml_data = {
                "milestones": [
                    {
                        "title": "测试里程碑",
                        "description": "测试里程碑描述",
                        "tasks": [{"title": "任务1", "description": "任务1描述"}, {"title": "任务2", "description": "任务2描述"}],
                    }
                ]
            }
            roadmap_id = "roadmap-123"
            import_stats = {"milestones": {"success": 0, "failed": 0}, "tasks": {"success": 0, "failed": 0}}

            # 模拟_process_milestone返回一个milestone_id
            with patch.object(importer, "_process_milestone", return_value="milestone-456"):
                # 执行测试
                importer.import_milestones(yaml_data, roadmap_id, import_stats)

                # 验证调用
                self.mock_roadmap_service.get_or_create_implicit_story_for_milestone.assert_called_once_with(
                    self.mock_session, "milestone-456", "测试里程碑", roadmap_id
                )

                # 验证TaskImporter.import_tasks被正确调用，且传入了story_id
                mock_task_importer.import_tasks.assert_called_once()
                actual_call = mock_task_importer.import_tasks.call_args
                self.assertEqual(actual_call[1]["story_id"], "story-123")
                self.assertEqual(actual_call[1]["milestone_id"], "milestone-456")
                self.assertEqual(actual_call[1]["roadmap_id"], roadmap_id)

    def test_roadmap_service_get_or_create_implicit_story(self):
        """测试RoadmapService.get_or_create_implicit_story_for_milestone方法"""
        # 配置mock
        service = RoadmapService()
        service.story_repo = self.mock_story_repo
        service.epic_repo = self.mock_epic_repo
        service.get_now = MagicMock(return_value="2023-01-01T00:00:00")

        # 配置story_repo.get_by_title_and_roadmap_id的行为，模拟不存在隐式Story
        self.mock_story_repo.get_by_title_and_roadmap_id.return_value = None

        # 配置epic_repo.get_by_roadmap_id的行为，模拟存在Epic
        mock_epic = MagicMock()
        mock_epic.id = "epic-789"
        mock_epic.title = "测试Epic"
        self.mock_epic_repo.get_by_roadmap_id.return_value = [mock_epic]

        # 配置story_repo.create的行为
        mock_story = MagicMock()
        mock_story.id = "story-123"
        self.mock_story_repo.create.return_value = mock_story

        # 执行测试
        result = service.get_or_create_implicit_story_for_milestone(self.mock_session, "milestone-456", "测试里程碑", "roadmap-123")

        # 验证结果
        self.assertEqual(result, "story-123")

        # 验证调用
        expected_title = "[隐式] 测试里程碑 下的任务"
        self.mock_story_repo.get_by_title_and_roadmap_id.assert_called_once_with(self.mock_session, expected_title, "roadmap-123")

        self.mock_epic_repo.get_by_roadmap_id.assert_called_once_with(self.mock_session, "roadmap-123")

        # 验证创建Story的调用参数
        create_call = self.mock_story_repo.create.call_args
        self.assertEqual(create_call[1]["title"], expected_title)
        self.assertEqual(create_call[1]["epic_id"], "epic-789")
        self.assertTrue(create_call[1]["is_implicit"])

    def test_get_or_create_implicit_story_existing(self):
        """测试当隐式Story已存在时的行为"""
        # 配置mock
        service = RoadmapService()
        service.story_repo = self.mock_story_repo

        # 配置story_repo.get_by_title_and_roadmap_id的行为，模拟存在隐式Story
        mock_story = MagicMock()
        mock_story.id = "existing-story-123"
        self.mock_story_repo.get_by_title_and_roadmap_id.return_value = mock_story

        # 执行测试
        result = service.get_or_create_implicit_story_for_milestone(self.mock_session, "milestone-456", "测试里程碑", "roadmap-123")

        # 验证结果
        self.assertEqual(result, "existing-story-123")

        # 验证get_by_title_and_roadmap_id被调用，但create未被调用
        expected_title = "[隐式] 测试里程碑 下的任务"
        self.mock_story_repo.get_by_title_and_roadmap_id.assert_called_once_with(self.mock_session, expected_title, "roadmap-123")
        self.mock_epic_repo.get_by_roadmap_id.assert_not_called()
        self.mock_story_repo.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
