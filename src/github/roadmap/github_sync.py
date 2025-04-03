"""
GitHub同步工具

提供roadmap.yaml与GitHub项目之间的数据同步功能。
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from ..api import GitHubClient
from .models import Milestone, Roadmap, Task


class GitHubSync:
    """GitHub同步工具，处理roadmap.yaml与GitHub项目之间的数据同步"""

    def __init__(self, github_client: GitHubClient = None, owner: str = None, repo: str = None):
        """
        初始化GitHub同步工具

        Args:
            github_client: GitHub API客户端
            owner: GitHub仓库所有者
            repo: GitHub仓库名称
        """
        self.github_client = github_client or GitHubClient()
        self.owner = owner or os.environ.get("GITHUB_OWNER")
        self.repo = repo or os.environ.get("GITHUB_REPO")

        if not self.owner or not self.repo:
            raise ValueError("未提供GitHub仓库信息")

    def sync_milestone_to_github(self, milestone: Milestone) -> Optional[Dict[str, Any]]:
        """
        将里程碑同步到GitHub

        Args:
            milestone: 里程碑数据

        Returns:
            Dict[str, Any]: GitHub里程碑数据
        """
        # 查找是否存在同名里程碑
        github_milestones = self.github_client.get(
            f"repos/{self.owner}/{self.repo}/milestones", params={"state": "all"}
        )

        existing_milestone = None
        for gm in github_milestones:
            if gm["title"] == milestone.name:
                existing_milestone = gm
                break

        # 准备里程碑数据
        milestone_data = {
            "title": milestone.name,
            "description": milestone.description,
            "due_on": milestone.end_date,
            "state": "open" if milestone.status in ["planned", "in_progress"] else "closed",
        }

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

    def sync_task_to_github(
        self, task: Task, milestone_number: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        将任务同步到GitHub Issue

        Args:
            task: 任务数据
            milestone_number: GitHub里程碑编号

        Returns:
            Dict[str, Any]: GitHub Issue数据
        """
        # 查找对应的里程碑
        if not milestone_number:
            github_milestones = self.github_client.get(
                f"repos/{self.owner}/{self.repo}/milestones", params={"state": "all"}
            )

            # 查找任务所属里程碑
            for milestone in github_milestones:
                if milestone["title"] == task.milestone:
                    milestone_number = milestone["number"]
                    break

        # 查找是否存在同名Issue
        github_issues = self.github_client.get(
            f"repos/{self.owner}/{self.repo}/issues", params={"state": "all"}
        )

        existing_issue = None
        for issue in github_issues:
            if issue.get("title") == f"[{task.id}] {task.title}":
                existing_issue = issue
                break

        # 准备Issue数据
        issue_data = {
            "title": f"[{task.id}] {task.title}",
            "body": task.description,
            "milestone": milestone_number,
            "state": "open" if task.status in ["todo", "in_progress"] else "closed",
            "labels": [task.priority, f"status:{task.status}"],
        }

        # 如果有指派人，添加到Issue数据
        if task.assignees:
            issue_data["assignees"] = task.assignees

        # 更新或创建Issue
        if existing_issue:
            return self.github_client.patch(
                f"repos/{self.owner}/{self.repo}/issues/{existing_issue['number']}", json=issue_data
            )
        else:
            return self.github_client.post(
                f"repos/{self.owner}/{self.repo}/issues", json=issue_data
            )

    def sync_roadmap_to_github(
        self, roadmap: Roadmap
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        将整个路线图同步到GitHub

        Args:
            roadmap: 路线图数据

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
                (同步的里程碑列表, 同步的任务列表)
        """
        synced_milestones = []
        synced_tasks = []

        # 同步里程碑
        milestone_mapping = {}  # 路线图里程碑ID到GitHub里程碑number的映射
        for milestone in roadmap.milestones:
            github_milestone = self.sync_milestone_to_github(milestone)
            if github_milestone:
                synced_milestones.append(github_milestone)
                milestone_mapping[milestone.id] = github_milestone["number"]

        # 同步任务
        for task in roadmap.tasks:
            milestone_number = milestone_mapping.get(task.milestone)
            github_task = self.sync_task_to_github(task, milestone_number)
            if github_task:
                synced_tasks.append(github_task)

        return synced_milestones, synced_tasks

    def sync_github_to_roadmap(self, roadmap: Roadmap) -> Roadmap:
        """
        将GitHub项目数据同步到路线图

        Args:
            roadmap: 当前路线图数据

        Returns:
            Roadmap: 更新后的路线图数据
        """
        # 获取GitHub里程碑
        github_milestones = self.github_client.get(
            f"repos/{self.owner}/{self.repo}/milestones", params={"state": "all"}
        )

        # 获取GitHub Issues
        github_issues = self.github_client.get(
            f"repos/{self.owner}/{self.repo}/issues", params={"state": "all"}
        )

        # 更新里程碑
        milestone_mapping = {}  # GitHub里程碑number到路线图里程碑ID的映射
        for github_milestone in github_milestones:
            # 查找对应的路线图里程碑
            matching_milestone = None
            for milestone in roadmap.milestones:
                if milestone.name == github_milestone["title"]:
                    matching_milestone = milestone
                    milestone_mapping[github_milestone["number"]] = milestone.id
                    break

            # 如果找到匹配的里程碑，更新状态
            if matching_milestone:
                matching_milestone.description = (
                    github_milestone["description"] or matching_milestone.description
                )
                matching_milestone.end_date = (
                    github_milestone["due_on"].split("T")[0]
                    if github_milestone["due_on"]
                    else matching_milestone.end_date
                )
                matching_milestone.status = (
                    "completed"
                    if github_milestone["state"] == "closed"
                    else (
                        "in_progress" if matching_milestone.status == "in_progress" else "planned"
                    )
                )

        # 更新任务
        for github_issue in github_issues:
            # 解析Issue标题，提取任务ID
            title = github_issue["title"]
            task_id = None
            if title.startswith("[") and "]" in title:
                task_id = title[1 : title.index("]")]

            # 查找对应的路线图任务
            matching_task = None
            if task_id:
                matching_task = roadmap.get_task_by_id(task_id)

            # 如果找到匹配的任务，更新状态
            if matching_task:
                # 更新状态
                if github_issue["state"] == "closed":
                    matching_task.status = "completed"
                else:
                    # 检查状态标签
                    for label in github_issue["labels"]:
                        if label["name"].startswith("status:"):
                            matching_task.status = label["name"][7:]  # 去掉'status:'前缀
                            break

                # 更新优先级
                for label in github_issue["labels"]:
                    if label["name"] in ["P0", "P1", "P2", "P3"]:
                        matching_task.priority = label["name"]
                        break

                # 更新指派人
                matching_task.assignees = [
                    assignee["login"] for assignee in github_issue["assignees"]
                ]

                # 更新里程碑
                if (
                    github_issue["milestone"]
                    and github_issue["milestone"]["number"] in milestone_mapping
                ):
                    matching_task.milestone = milestone_mapping[github_issue["milestone"]["number"]]

        # 更新里程碑进度
        for milestone in roadmap.milestones:
            roadmap.update_milestone_progress(milestone.id)

        return roadmap
