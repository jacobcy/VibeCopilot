#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GitHub无映射Issue同步功能
"""

import unittest
from unittest.mock import MagicMock, call, patch

from src.db.repositories import EpicRepository, MilestoneRepository, StoryRepository, TaskRepository
from src.db.repositories.mapping_repository import EntityMappingRepository
from src.sync.github_sync import GitHubSyncService


class TestGitHubUnmappedIssues(unittest.TestCase):
    """测试GitHub无映射Issue同步功能"""

    def setUp(self):
        """测试前设置"""
        self.mock_session = MagicMock()
        self.mock_roadmap_service = MagicMock()
        self.mock_api_facade = MagicMock()

        # 为每个 repo 创建独立的 mock 对象
        self.mock_story_repo = MagicMock(spec=StoryRepository)
        self.mock_epic_repo = MagicMock(spec=EpicRepository)
        self.mock_milestone_repo = MagicMock(spec=MilestoneRepository)
        self.mock_task_repo = MagicMock(spec=TaskRepository)
        self.mock_mapping_repo = MagicMock(spec=EntityMappingRepository)

        # 配置roadmap_service的属性以使用这些独立的 mocks
        self.mock_roadmap_service.story_repo = self.mock_story_repo
        self.mock_roadmap_service.epic_repo = self.mock_epic_repo
        self.mock_roadmap_service.milestone_repo = self.mock_milestone_repo  # 确保 GitHubSyncService 使用这个
        self.mock_roadmap_service.task_repo = self.mock_task_repo

        # 配置时间方法
        self.mock_roadmap_service.get_now.return_value = "2023-01-01T00:00:00"

    @patch("src.sync.github_sync.session_scope")
    @patch("src.status.service.StatusService")
    def test_sync_unmapped_github_issue(self, mock_status_service_class, mock_session_scope):
        """测试同步无映射的GitHub Issues"""
        # 配置session_scope的模拟
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = self.mock_session
        mock_session_scope.return_value = mock_session_context

        # 配置StatusService
        mock_status_service = MagicMock()
        mock_status_service.get_instance.return_value = mock_status_service
        mock_status_service_class.get_instance.return_value = mock_status_service

        mock_project_state = MagicMock()
        mock_status_service.project_state = mock_project_state

        # 配置project_state的github_config
        github_config = {
            "owner": "test-owner",
            "repo": "test-repo",
            "project_id": "project-node-id-123",
            "project_number": 1,
            "project_title": "Test Project",
        }
        mock_project_state.get_active_roadmap_backend_config.return_value = github_config

        # 实例化GitHubSyncService
        # 确保GitHubSyncService内部也使用我们模拟的仓库实例
        with patch("src.sync.github_sync.EntityMappingRepository", return_value=self.mock_mapping_repo):
            with patch("src.sync.github_sync.GitHubApiFacade", return_value=self.mock_api_facade):
                # 在GitHubSyncService实例化时，它会创建自己的MilestoneRepository等实例。
                # 我们需要确保这些也被mock掉，或者让它使用我们传入的roadmap_service中的mocked repos。
                # 为了简单起见，这里我们假设GitHubSyncService会使用传入的roadmap_service中的repos。
                # 如果不是这样，我们可能需要patch GitHubSyncService内部的仓库实例化。

                github_sync = GitHubSyncService(self.mock_roadmap_service)
                # 显式地将 GitHubSyncService 内部的 _milestone_repo 等指向我们 setUp 中创建的 mock 对象
                # 这样可以确保所有仓库操作都通过我们控制的 mock 进行。
                github_sync._milestone_repo = self.mock_milestone_repo
                github_sync._epic_repo = self.mock_epic_repo
                github_sync._story_repo = self.mock_story_repo
                github_sync.mapping_repo = self.mock_mapping_repo

                # 配置API facade方法
                self.mock_api_facade.get_milestones.return_value = [
                    {"number": 1, "title": "测试里程碑", "description": "测试里程碑描述", "state": "open", "node_id": "milestone-node-id-456"}
                ]

                # 配置无映射Issues
                self.mock_api_facade.get_all_project_items_by_node_id.return_value = [
                    {
                        "number": 42,
                        "title": "无映射任务",
                        "body": "任务描述",
                        "state": "open",
                        "node_id": "issue-node-id-789",
                        "labels": [],  # 没有epic或story标签
                        "milestone": {"number": 1, "title": "测试里程碑", "description": "测试里程碑描述", "state": "open", "node_id": "milestone-node-id-456"},
                    }
                ]

                # 配置映射查询结果 - 任务没有映射
                self.mock_mapping_repo.get_mapping_by_remote_id.return_value = None
                self.mock_mapping_repo.get_mapping_by_remote_number.return_value = None

                # 配置里程碑查询结果 (get_by_title_and_roadmap_id)
                mock_local_milestone = MagicMock()
                mock_local_milestone.id = "local-milestone-id-123"
                mock_local_milestone.title = "测试里程碑"
                # self.mock_milestone_repo.get_by_title_and_roadmap_id.return_value = mock_local_milestone
                # GitHubSyncService 内部的 _milestone_repo 才是实际调用的，所以应该 mock 它
                github_sync._milestone_repo.get_by_title_and_roadmap_id.return_value = mock_local_milestone

                # 配置 MilestoneRepository 的 update 和 get_by_id (因为 update 会调用 get_by_id)
                # 当 github_sync._milestone_repo.update 被调用时:
                # 1. 其内部的 get_by_id 需要返回一个 mock 对象
                mock_milestone_for_internal_get_by_id = MagicMock()
                mock_milestone_for_internal_get_by_id.id = mock_local_milestone.id  # 确保ID一致
                github_sync._milestone_repo.get_by_id.return_value = mock_milestone_for_internal_get_by_id
                # 2. update 方法本身返回一个 mock 对象
                github_sync._milestone_repo.update.return_value = mock_milestone_for_internal_get_by_id

                # 配置隐式Story创建
                self.mock_roadmap_service.get_or_create_implicit_story_for_milestone.return_value = "local-implicit-story-id-456"

                # 配置任务创建
                mock_task = MagicMock()
                mock_task.id = "local-task-id-789"
                self.mock_roadmap_service.task_repo.create.return_value = mock_task

                # 执行测试
                result = github_sync.sync_status_from_github("roadmap-123")

                # 检查结果
                self.assertEqual(result["status"], "success")
                self.assertIn("new_entities_created", result["data"]["stats"].keys())
                self.assertEqual(result["data"]["stats"]["new_entities_created"], 1)

                # 验证调用
                # 1. 验证映射查询
                self.mock_mapping_repo.get_mapping_by_remote_id.assert_called_with(self.mock_session, "issue-node-id-789", "github")

                # 2. 验证里程碑查询
                self.mock_milestone_repo.get_by_title_and_roadmap_id.assert_called_with(self.mock_session, "测试里程碑", "roadmap-123")

                # 3. 验证隐式Story创建
                self.mock_roadmap_service.get_or_create_implicit_story_for_milestone.assert_called_with(
                    self.mock_session, "local-milestone-id-123", "测试里程碑", "roadmap-123"
                )

                # 4. 验证任务创建 (注意：由于map_github_issue_to_task_update是复杂函数，我们这里不验证具体结构)
                self.mock_roadmap_service.task_repo.create.assert_called()
                create_call = self.mock_roadmap_service.task_repo.create.call_args
                self.assertEqual(create_call[1]["story_id"], "local-implicit-story-id-456")

                # 5. 验证映射创建
                self.mock_mapping_repo.create_mapping.assert_called_with(
                    self.mock_session,
                    local_entity_id="local-task-id-789",
                    local_entity_type="task",
                    backend_type="github",
                    remote_entity_id="issue-node-id-789",
                    remote_entity_number="42",
                    local_project_id="roadmap-123",
                    remote_project_id="project-node-id-123",
                    remote_project_context="Test Project",
                )


if __name__ == "__main__":
    unittest.main()
