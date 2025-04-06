#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
风险分析模块.

评估GitHub项目的风险和阻塞问题。
"""

import datetime
from typing import Any, Dict, List, Tuple

from ..utils import is_date_passed, parse_date


def analyze_risks(project_data: Dict[str, Any]) -> Dict[str, Any]:
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
    delayed_tasks, delayed_milestones = check_delayed_items(open_issues, milestones, today)

    # 计算延期率
    delayed_rate = round((delayed_tasks / len(open_issues)) * 100, 2) if open_issues else 0

    # 计算风险得分
    risk_level, risk_score = calculate_risk_level(delayed_rate, blocked_tasks)

    return {
        "blocked_tasks": blocked_tasks,
        "delayed_tasks": delayed_tasks,
        "delayed_milestones": delayed_milestones,
        "delayed_rate": delayed_rate,
        "risk_level": risk_level,
        "risk_score": risk_score,
    }


def check_delayed_items(
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
        if issue.get("due_on") and is_date_passed(parse_date(issue["due_on"])):
            delayed_tasks += 1
            continue

        # 检查issue所属里程碑是否已过期
        milestone = issue.get("milestone")
        if (
            milestone
            and milestone.get("due_on")
            and is_date_passed(parse_date(milestone["due_on"]))
        ):
            delayed_tasks += 1

    # 检查过期里程碑
    for milestone in milestones:
        if (
            milestone.get("state") == "open"
            and milestone.get("due_on")
            and is_date_passed(parse_date(milestone["due_on"]))
        ):
            delayed_milestones += 1

    return delayed_tasks, delayed_milestones


def calculate_risk_level(delayed_rate: float, blocked_tasks: int) -> Tuple[str, int]:
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
