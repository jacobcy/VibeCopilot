"""
GitHub连接器模块

简化版的GitHub同步连接器，专注于将Markdown解析的数据传递给GitHub项目模块。
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from scripts.github_project.api import GitHubClient
from scripts.github_project.api.issues_client import GitHubIssuesClient

from .markdown_parser import load_sync_status, read_all_stories, save_sync_status
from .models import Milestone, Roadmap, Task


class GitHubConnector:
    """GitHub连接器, 专注于Markdown数据和GitHub项目系统的连接"""

    def __init__(self, github_client: GitHubClient = None, owner: str = None, repo: str = None):
        """
        初始化GitHub连接器

        Args:
            github_client: GitHub API客户端
            owner: GitHub仓库所有者
            repo: GitHub仓库名称
        """
        self.github_client = github_client or GitHubClient()
        self.issues_client = GitHubIssuesClient()
        self.owner = owner or os.environ.get("GITHUB_OWNER")
        self.repo = repo or os.environ.get("GITHUB_REPO")

        if not self.owner or not self.repo:
            raise ValueError("未提供GitHub仓库信息")

    def get_markdown_data(self) -> Dict[str, Any]:
        """
        从Markdown文件获取数据

        Returns:
            Dict[str, Any]: 解析后的数据
        """
        return read_all_stories()

    def sync_to_github(self) -> Tuple[int, int]:
        """
        将Markdown数据同步到GitHub

        Returns:
            Tuple[int, int]: (同步的里程碑数量, 同步的任务数量)
        """
        # 读取数据
        data = self.get_markdown_data()

        # 同步里程碑
        milestone_count = 0
        milestone_mapping = {}  # 里程碑ID到GitHub里程碑编号的映射

        print(f"开始同步 {len(data.get('milestones', []))} 个里程碑...")
        for m_data in data.get("milestones", []):
            try:
                # 准备里程碑数据
                milestone_data = {
                    "title": m_data.get("name", ""),
                    "description": m_data.get("description", ""),
                    "state": "open"
                    if m_data.get("status") in ["planned", "in_progress"]
                    else "closed",
                }

                # 添加due_on字段（如果有日期）
                if m_data.get("end_date"):
                    if "T" not in m_data["end_date"]:
                        milestone_data["due_on"] = f"{m_data['end_date']}T23:59:59Z"
                    else:
                        milestone_data["due_on"] = m_data["end_date"]

                # 创建或更新里程碑
                github_milestone = self._create_or_update_milestone(
                    m_data.get("id", ""), milestone_data
                )
                if github_milestone:
                    milestone_count += 1
                    milestone_mapping[m_data.get("id", "")] = github_milestone["number"]
                    print(f"✅ 成功同步里程碑: {m_data.get('name', '')}")
            except Exception as e:
                print(f"❌ 里程碑同步出错 [{m_data.get('id', '')}]: {str(e)}")

        # 同步任务
        task_count = 0
        print(f"\n开始同步 {len(data.get('tasks', []))} 个任务...")
        for t_data in data.get("tasks", []):
            try:
                milestone_number = milestone_mapping.get(t_data.get("milestone", ""))

                # 获取标签列表
                labels = []
                if t_data.get("priority"):
                    labels.append(t_data.get("priority"))
                if t_data.get("status"):
                    labels.append(f"status:{t_data.get('status')}")
                if t_data.get("epic"):
                    labels.append(f"epic:{t_data.get('epic')}")

                # 准备任务数据
                issue_data = {
                    "title": f"[{t_data.get('id', '')}] {t_data.get('title', '')}",
                    "body": t_data.get("description", ""),
                    "state": "open"
                    if t_data.get("status") in ["todo", "in_progress"]
                    else "closed",
                    "labels": labels,
                    "assignees": t_data.get("assignees", []),
                    "milestone": milestone_number,
                }

                # 创建或更新任务
                github_issue = self._create_or_update_issue(t_data.get("id", ""), issue_data)
                if github_issue:
                    task_count += 1
                    print(f"✅ 成功同步任务: [{t_data.get('id', '')}] {t_data.get('title', '')}")
            except Exception as e:
                print(f"❌ 任务同步出错 [{t_data.get('id', '')}]: {str(e)}")

        print(
            f"\n同步完成: {milestone_count}/{len(data.get('milestones', []))} 个里程碑, "
            f"{task_count}/{len(data.get('tasks', []))} 个任务"
        )

        return milestone_count, task_count

    def _create_or_update_milestone(
        self, milestone_id: str, milestone_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建或更新里程碑"""
        try:
            # 查找是否存在同名里程碑
            github_milestones = self.github_client.get(
                f"repos/{self.owner}/{self.repo}/milestones", params={"state": "all"}
            )

            existing_milestone = None
            for gm in github_milestones:
                if gm["title"] == milestone_data["title"]:
                    existing_milestone = gm
                    break

            # 更新或创建里程碑
            if existing_milestone:
                return self.github_client.patch(
                    f"repos/{self.owner}/{self.repo}/milestones/{existing_milestone['number']}",
                    json=milestone_data,
                )
            else:
                return self.github_client.post(
                    f"repos/{self.owner}/{self.repo}/milestones", json=milestone_data
                )
        except Exception as e:
            print(f"操作里程碑失败: {str(e)}")
            return None

    def _create_or_update_issue(
        self, task_id: str, issue_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """创建或更新Issue"""
        try:
            # 查找是否存在同名Issue
            github_issues = self.github_client.get(
                f"repos/{self.owner}/{self.repo}/issues", params={"state": "all"}
            )

            existing_issue = None
            for issue in github_issues:
                if issue.get("title") == issue_data["title"]:
                    existing_issue = issue
                    break

            # 更新或创建Issue
            if existing_issue:
                return self.github_client.patch(
                    f"repos/{self.owner}/{self.repo}/issues/{existing_issue['number']}",
                    json=issue_data,
                )
            else:
                return self.github_client.post(
                    f"repos/{self.owner}/{self.repo}/issues", json=issue_data
                )
        except Exception as e:
            print(f"操作任务失败: {str(e)}")
            return None

    # 兼容旧接口
    def sync_roadmap_to_github(self) -> Tuple[int, int]:
        """兼容旧接口的同步方法"""
        return self.sync_to_github()
