#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
进度分析模块.

分析GitHub项目的进度情况。
"""

import datetime
from typing import Any, Dict, List

from ...utils import parse_date


def analyze_progress(project_data: Dict[str, Any]) -> Dict[str, Any]:
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
    completion_rate = round((completed_issues / total_issues) * 100, 2) if total_issues > 0 else 0

    # 按状态分类任务
    status_distribution = categorize_by_status(issues)

    # 分析里程碑进度
    milestones_progress = analyze_milestones_progress(issues, project_data.get("milestones", []))

    return {
        "completed": completed_issues,
        "total": total_issues,
        "completion_rate": completion_rate,
        "status_distribution": status_distribution,
        "milestones_progress": milestones_progress,
    }


def categorize_by_status(issues: List[Dict[str, Any]]) -> Dict[str, int]:
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


def analyze_milestones_progress(
    issues: List[Dict[str, Any]], milestones: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """分析里程碑进度.

    Args:
        issues: Issue列表
        milestones: 里程碑列表

    Returns:
        Dict[str, Dict[str, Any]]: 里程碑进度
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
