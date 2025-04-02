#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目分析模块.

分析GitHub项目的进度、质量和风险。
"""

import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from ...github.api import GitHubClient, GitHubIssuesClient, GitHubProjectsClient


class ProjectAnalyzer:
    """项目分析器."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        projects_client: Optional[GitHubProjectsClient] = None,
        issues_client: Optional[GitHubIssuesClient] = None,
    ):
        """初始化项目分析器.

        Args:
            github_client: GitHub API客户端
            projects_client: GitHub Projects API客户端
            issues_client: GitHub Issues API客户端
        """
        self.github_client = github_client or GitHubClient()
        self.projects_client = projects_client or GitHubProjectsClient()
        self.issues_client = issues_client or GitHubIssuesClient()

    def analyze_project(
        self, owner: str, repo: str, project_number: int, metrics: List[str] = None
    ) -> Dict[str, Any]:
        """分析项目状态.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            metrics: 要分析的指标列表，默认全部分析

        Returns:
            Dict[str, Any]: 分析结果
        """
        # 默认分析所有指标
        if metrics is None:
            metrics = ["progress", "quality", "risks"]

        # 获取项目数据
        project_data = self._get_project_data(owner, repo, project_number)

        # 分析结果
        analysis = {}

        if "progress" in metrics:
            analysis["progress"] = self.analyze_progress(project_data)

        if "quality" in metrics:
            analysis["quality"] = self.analyze_quality(project_data)

        if "risks" in metrics:
            analysis["risks"] = self.analyze_risks(project_data)

        return analysis

    def _get_project_data(self, owner: str, repo: str, project_number: int) -> Dict[str, Any]:
        """获取项目数据.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号

        Returns:
            Dict[str, Any]: 项目数据
        """
        # 获取项目数据
        project_v2_data = self.projects_client.get_project_v2(owner, repo, project_number)

        # 获取仓库issue数据
        issues = self.issues_client.get_issues(owner, repo, state="all")

        # 获取仓库PR数据
        pull_requests = self.github_client.get(
            f"repos/{owner}/{repo}/pulls", params={"state": "all"}
        )
        if not isinstance(pull_requests, list):
            pull_requests = []

        # 获取仓库里程碑数据
        milestones = self.github_client.get(
            f"repos/{owner}/{repo}/milestones", params={"state": "all"}
        )
        if not isinstance(milestones, list):
            milestones = []

        return {
            "project_v2": project_v2_data,
            "issues": issues,
            "pull_requests": pull_requests,
            "milestones": milestones,
        }

    def analyze_progress(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析项目进度.

        Args:
            project_data: 项目数据

        Returns:
            Dict[str, Any]: 进度分析结果
        """
        issues = project_data.get("issues", [])

        # 计算任务完成情况
        total_issues = len(issues)
        completed_issues = sum(1 for issue in issues if issue.get("state") == "closed")
        completion_rate = (
            round((completed_issues / total_issues) * 100, 2) if total_issues > 0 else 0
        )

        # 按状态分类任务
        status_distribution = self._categorize_by_status(issues)

        # 分析里程碑进度
        milestones_progress = self._analyze_milestones_progress(
            issues, project_data.get("milestones", [])
        )

        return {
            "completed": completed_issues,
            "total": total_issues,
            "completion_rate": completion_rate,
            "status_distribution": status_distribution,
            "milestones_progress": milestones_progress,
        }

    def _categorize_by_status(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """按状态分类任务.

        Args:
            issues: Issue列表

        Returns:
            Dict[str, int]: 状态分布
        """
        status_count = {}

        for issue in issues:
            # 获取基本状态 (open/closed)
            base_state = issue.get("state", "unknown")

            # 尝试获取项目中的自定义状态
            custom_status = None
            if "project_card" in issue and issue["project_card"]:
                project_card = issue["project_card"]
                if "column_name" in project_card:
                    custom_status = project_card["column_name"]

            # 使用自定义状态或基本状态
            status = custom_status or base_state

            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1

        return status_count

    def _analyze_milestones_progress(
        self, issues: List[Dict[str, Any]], milestones: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """分析里程碑进度.

        Args:
            issues: Issue列表
            milestones: 里程碑列表

        Returns:
            Dict[str, Dict[str, Union[int, float]]]: 里程碑进度
        """
        milestones_progress = {}

        # 创建里程碑映射
        milestone_map = {milestone["number"]: milestone for milestone in milestones}

        # 统计每个里程碑的任务
        for issue in issues:
            milestone_info = issue.get("milestone")
            if not milestone_info:
                continue

            milestone_number = milestone_info.get("number")
            if milestone_number is None:
                continue

            milestone_title = milestone_info.get("title", f"里程碑 {milestone_number}")

            if milestone_title not in milestones_progress:
                milestones_progress[milestone_title] = {
                    "total": 0,
                    "completed": 0,
                    "completion_rate": 0,
                }

                # 添加截止日期信息
                if milestone_number in milestone_map:
                    due_on = milestone_map[milestone_number].get("due_on")
                    if due_on:
                        milestones_progress[milestone_title]["due_date"] = due_on

            # 更新计数
            milestones_progress[milestone_title]["total"] += 1
            if issue.get("state") == "closed":
                milestones_progress[milestone_title]["completed"] += 1

        # 计算完成率
        for milestone, data in milestones_progress.items():
            total = data["total"]
            completed = data["completed"]
            data["completion_rate"] = round((completed / total) * 100, 2) if total > 0 else 0

        return milestones_progress

    def analyze_quality(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析项目质量.

        Args:
            project_data: 项目数据

        Returns:
            Dict[str, Any]: 质量分析结果
        """
        pull_requests = project_data.get("pull_requests", [])

        # 计算PR合并率
        closed_prs = [pr for pr in pull_requests if pr.get("state") == "closed"]
        total_closed_prs = len(closed_prs)
        merged_prs = sum(1 for pr in closed_prs if pr.get("merged"))
        pr_merge_rate = (
            round((merged_prs / total_closed_prs) * 100, 2) if total_closed_prs > 0 else 0
        )

        # 计算平均评论数
        review_comments_total = sum(pr.get("review_comments", 0) for pr in pull_requests)
        review_comments_avg = (
            round(review_comments_total / len(pull_requests), 2) if pull_requests else 0
        )

        # 假设的测试覆盖率数据 (实际项目中可从CI系统获取)
        test_coverage = 75.5

        return {
            "pr_merge_rate": pr_merge_rate,
            "review_comments_avg": review_comments_avg,
            "test_coverage": test_coverage,
            "merged_prs": merged_prs,
            "total_closed_prs": total_closed_prs,
        }

    def analyze_risks(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析项目风险.

        Args:
            project_data: 项目数据

        Returns:
            Dict[str, Any]: 风险分析结果
        """
        issues = project_data.get("issues", [])
        milestones = project_data.get("milestones", [])

        # 找出开放的issues
        open_issues = [issue for issue in issues if issue.get("state") == "open"]

        # 检查阻塞任务
        blocked_tasks = sum(
            1
            for issue in open_issues
            if any(
                label.get("name", "").lower() in ["blocked", "blocker"]
                for label in issue.get("labels", [])
            )
        )

        # 检查延期任务
        today = datetime.datetime.now(datetime.timezone.utc)
        delayed_tasks, delayed_milestones = self._check_delayed_items(
            open_issues, milestones, today
        )

        # 计算延期率
        delayed_rate = round((delayed_tasks / len(open_issues)) * 100, 2) if open_issues else 0

        # 计算风险得分
        risk_level, risk_score = self._calculate_risk_level(delayed_rate, blocked_tasks)

        return {
            "blocked_tasks": blocked_tasks,
            "delayed_tasks": delayed_tasks,
            "delayed_milestones": delayed_milestones,
            "delayed_rate": delayed_rate,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

    def _check_delayed_items(
        self,
        issues: List[Dict[str, Any]],
        milestones: List[Dict[str, Any]],
        today: datetime.datetime,
    ) -> Tuple[int, int]:
        """检查延期的任务和里程碑.

        Args:
            issues: Issue列表
            milestones: 里程碑列表
            today: 当前日期

        Returns:
            Tuple[int, int]: 延期任务数和延期里程碑数
        """
        delayed_tasks = 0
        delayed_milestones = 0

        # 检查有截止日期的issue
        for issue in issues:
            # 检查issue本身是否有截止日期
            if issue.get("due_on") and self._parse_date(issue["due_on"]) < today:
                delayed_tasks += 1
                continue

            # 检查issue所属里程碑是否已过期
            milestone = issue.get("milestone")
            if (
                milestone
                and milestone.get("due_on")
                and self._parse_date(milestone["due_on"]) < today
            ):
                delayed_tasks += 1

        # 检查过期里程碑
        for milestone in milestones:
            if (
                milestone.get("state") == "open"
                and milestone.get("due_on")
                and self._parse_date(milestone["due_on"]) < today
            ):
                delayed_milestones += 1

        return delayed_tasks, delayed_milestones

    def _parse_date(self, date_str: str) -> datetime.datetime:
        """解析日期字符串.

        Args:
            date_str: 日期字符串

        Returns:
            datetime.datetime: 日期对象
        """
        if not date_str:
            return datetime.datetime.now(datetime.timezone.utc)

        try:
            return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            # 回退到当前日期
            return datetime.datetime.now(datetime.timezone.utc)

    def _calculate_risk_level(self, delayed_rate: float, blocked_tasks: int) -> Tuple[str, int]:
        """计算风险等级.

        Args:
            delayed_rate: 延期任务比例
            blocked_tasks: 阻塞任务数量

        Returns:
            Tuple[str, int]: 风险等级和风险得分
        """
        risk_score = 0

        # 延期任务比例
        if delayed_rate > 20:
            risk_score += 2
        elif delayed_rate > 10:
            risk_score += 1

        # 阻塞任务数量
        if blocked_tasks > 5:
            risk_score += 2
        elif blocked_tasks > 2:
            risk_score += 1

        # 风险等级
        risk_level = "HIGH" if risk_score >= 3 else "MEDIUM" if risk_score >= 1 else "LOW"

        return risk_level, risk_score

    def generate_report(self, analysis: Dict[str, Any], format_type: str = "markdown") -> str:
        """生成分析报告.

        Args:
            analysis: 分析结果
            format_type: 报告格式类型

        Returns:
            str: 格式化的报告
        """
        if format_type == "markdown":
            return self._generate_markdown_report(analysis)
        elif format_type == "json":
            import json

            return json.dumps(analysis, indent=2)
        else:
            return str(analysis)

    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """生成Markdown格式的报告.

        Args:
            analysis: 分析结果

        Returns:
            str: Markdown格式的报告
        """
        report = ["# 项目分析报告", "", "## 总体状况"]

        # 总体状况
        if "progress" in analysis:
            completion_rate = analysis["progress"]["completion_rate"]
            report.append(f"- 完成度：{completion_rate}%")

        if "risks" in analysis:
            risk_level = analysis["risks"]["risk_level"]
            risk_style = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🚨"}
            report.append(f"- 风险等级：{risk_style.get(risk_level, '')} {risk_level}")

        if "quality" in analysis:
            quality = analysis["quality"]
            health_score = (
                quality["pr_merge_rate"] * 0.4
                + min(quality["review_comments_avg"] * 10, 100) * 0.3
                + quality["test_coverage"] * 0.3
            )
            report.append(f"- 健康指数：{round(health_score, 1)}/100")

        # 关键发现
        report.extend(["", "## 需要注意"])
        key_points = self._extract_key_points(analysis)
        for i, point in enumerate(key_points, 1):
            report.append(f"{i}. {point}")

        # 建议操作
        report.extend(["", "## 建议操作"])
        recommendations = self._generate_recommendations(analysis)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")

        # 详细分析
        if "progress" in analysis:
            report.extend(["", "## 进度详情"])
            progress = analysis["progress"]
            report.append(
                f"- 已完成任务：{progress['completed']}/{progress['total']} ({progress['completion_rate']}%)"
            )

            # 添加里程碑进度
            if "milestones_progress" in progress and progress["milestones_progress"]:
                report.append("")
                report.append("### 里程碑进度")
                report.append("")
                report.append("| 里程碑 | 完成率 | 总任务数 | 已完成 | 截止日期 |")
                report.append("| ------ | ------ | -------- | ------ | -------- |")

                for milestone, data in progress["milestones_progress"].items():
                    due_date = data.get("due_date", "未设置")
                    if isinstance(due_date, str) and due_date.endswith("Z"):
                        due_date = due_date[:-1].split("T")[0]

                    report.append(
                        f"| {milestone} | {data['completion_rate']}% | {data['total']} | {data['completed']} | {due_date} |"
                    )

        if "quality" in analysis:
            report.extend(["", "## 质量指标"])
            quality = analysis["quality"]
            report.append(f"- PR合并率：{quality['pr_merge_rate']}%")
            report.append(f"- 平均评论数：{quality['review_comments_avg']}")
            report.append(f"- 测试覆盖率：{quality['test_coverage']}%")

        if "risks" in analysis:
            report.extend(["", "## 风险评估"])
            risks = analysis["risks"]
            report.append(f"- 阻塞任务：{risks['blocked_tasks']}")
            report.append(f"- 延期任务：{risks['delayed_tasks']} (延期率: {risks['delayed_rate']}%)")
            report.append(f"- 延期里程碑：{risks.get('delayed_milestones', 0)}")

        return "\n".join(report)

    def _extract_key_points(self, analysis: Dict[str, Any]) -> List[str]:
        """提取关键发现点.

        Args:
            analysis: 分析结果

        Returns:
            List[str]: 关键发现点列表
        """
        key_points = []

        # 检查进度问题
        if "progress" in analysis:
            progress = analysis["progress"]
            completion_rate = progress["completion_rate"]

            if completion_rate < 50:
                key_points.append(f"项目进度缓慢，完成率仅为 {completion_rate}%")

            # 检查里程碑进度
            if "milestones_progress" in progress:
                delayed_milestones = []
                for name, data in progress["milestones_progress"].items():
                    if "due_date" in data and data["completion_rate"] < 50:
                        due_date = data["due_date"]
                        if isinstance(due_date, str):
                            try:
                                due_date = self._parse_date(due_date)
                                if due_date < datetime.datetime.now(datetime.timezone.utc):
                                    delayed_milestones.append(name)
                            except (ValueError, TypeError):
                                pass

                if delayed_milestones:
                    if len(delayed_milestones) == 1:
                        key_points.append(f"里程碑 '{delayed_milestones[0]}' 已延期但进度不足50%")
                    else:
                        key_points.append(f"{len(delayed_milestones)}个里程碑已延期但进度不足50%")

        # 检查风险问题
        if "risks" in analysis:
            risks = analysis["risks"]

            if risks["blocked_tasks"] > 0:
                key_points.append(f"有{risks['blocked_tasks']}个任务被阻塞，需要解决")

            if risks["delayed_rate"] > 20:
                key_points.append(f"延期任务比例较高({risks['delayed_rate']}%)，需要关注")

        # 检查质量问题
        if "quality" in analysis:
            quality = analysis["quality"]

            if quality["pr_merge_rate"] < 70:
                key_points.append(f"PR合并率较低({quality['pr_merge_rate']}%)，可能存在代码质量问题")

            if quality["test_coverage"] < 60:
                key_points.append(f"测试覆盖率不足({quality['test_coverage']}%)，需要增加测试")

        # 如果没有问题，添加一个正面评价
        if not key_points:
            key_points.append("项目状态良好，无明显问题")

        return key_points

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成建议操作.

        Args:
            analysis: 分析结果

        Returns:
            List[str]: 建议操作列表
        """
        recommendations = []

        # 基于进度的建议
        if "progress" in analysis:
            progress = analysis["progress"]
            completion_rate = progress["completion_rate"]

            if completion_rate < 50:
                recommendations.append("考虑调整项目范围或增加资源以提高进度")

            # 检查里程碑进度
            if "milestones_progress" in progress:
                low_progress_milestones = [
                    name
                    for name, data in progress["milestones_progress"].items()
                    if data["completion_rate"] < 40 and data.get("total", 0) > 0
                ]

                if low_progress_milestones and len(low_progress_milestones) <= 3:
                    milestone_names = ", ".join(f"'{name}'" for name in low_progress_milestones)
                    recommendations.append(f"重点关注进度较慢的里程碑: {milestone_names}")

        # 基于风险的建议
        if "risks" in analysis:
            risks = analysis["risks"]

            if risks["blocked_tasks"] > 0:
                recommendations.append("召开阻塞问题解决会议，解决阻塞任务")

            if risks["delayed_rate"] > 20:
                recommendations.append("审查延期任务，调整项目时间线或重新分配资源")

        # 基于质量的建议
        if "quality" in analysis:
            quality = analysis["quality"]

            if quality["pr_merge_rate"] < 70:
                recommendations.append("改进代码审查流程，提高PR质量和合并率")

            if quality["review_comments_avg"] < 2:
                recommendations.append("鼓励更多的代码审查反馈，提高代码质量")

            if quality["test_coverage"] < 60:
                recommendations.append("增加单元测试覆盖率，特别是关键功能模块")

        # 如果没有具体建议，添加一个通用建议
        if not recommendations:
            recommendations.append("保持当前的工作节奏和质量标准")

        return recommendations
