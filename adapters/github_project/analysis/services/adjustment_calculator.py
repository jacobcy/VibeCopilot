#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调整计算模块.

计算里程碑和项目时间线的调整。
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..utils import get_days_difference, is_date_passed, parse_date


def calculate_adjustments(
    analysis: Dict[str, Any], repo_data: Dict[str, Any], max_days: int
) -> Dict[str, Dict[str, Any]]:
    """计算时间线调整.

    Args:
        analysis: 项目分析结果
        repo_data: 仓库数据
        max_days: 最大调整天数

    Returns:
        Dict[str, Dict[str, Any]]: 调整计划
    """
    logger = logging.getLogger(__name__)
    logger.info("计算时间线调整")

    adjustments = {}

    # 如果没有进度或风险数据，则无法进行调整
    if "progress" not in analysis or "risks" not in analysis:
        logger.warning("分析结果中缺少进度或风险数据，无法进行调整")
        return adjustments

    # 获取里程碑进度数据
    milestones_progress = analysis["progress"].get("milestones_progress", {})

    # 获取风险评估
    risk_level = analysis["risks"].get("risk_level", "LOW")

    # 为每个里程碑计算调整幅度
    for milestone in repo_data["milestones"]:
        milestone_title = milestone.get("title", "")

        # 如果里程碑没有标题或截止日期，跳过
        if not milestone_title or not milestone.get("due_on"):
            continue

        # 获取里程碑进度数据
        progress_data = milestones_progress.get(
            milestone_title, {"completion_rate": 0, "total": 0, "completed": 0}
        )

        # 计算调整天数
        adjustment_days = calculate_adjustment_days(milestone, progress_data, risk_level)

        # 限制最大调整天数
        if adjustment_days > max_days:
            adjustment_days = max_days
        elif adjustment_days < -max_days // 3:  # 提前调整天数限制更严格
            adjustment_days = -max_days // 3

        # 记录调整
        if adjustment_days != 0:
            # 解析日期
            try:
                due_date = parse_date(milestone["due_on"])
                new_due_date = due_date + datetime.timedelta(days=adjustment_days)

                adjustments[milestone_title] = {
                    "milestone": milestone,
                    "original_due_date": due_date,
                    "adjustment_days": adjustment_days,
                    "new_due_date": new_due_date,
                }
            except Exception as e:
                logger.error(f"处理里程碑 '{milestone_title}' 日期时出错: {str(e)}")

    return adjustments


def calculate_adjustment_days(
    milestone: Dict[str, Any], progress_data: Dict[str, Any], risk_level: str
) -> int:
    """计算里程碑调整天数.

    Args:
        milestone: 里程碑数据
        progress_data: 进度数据
        risk_level: 风险等级

    Returns:
        int: 调整天数
    """
    # 如果没有任务，不做调整
    if progress_data.get("total", 0) == 0:
        return 0

    # 获取完成率
    completion_rate = progress_data.get("completion_rate", 0)

    # 解析日期
    try:
        due_date = parse_date(milestone["due_on"])
        create_date = parse_date(milestone.get("created_at", ""))
        today = datetime.datetime.now(datetime.timezone.utc)
    except Exception:
        return 0

    # 如果里程碑已过期，设置延期
    if is_date_passed(due_date):
        # 根据完成率决定延期时间
        if completion_rate < 50:
            return 14  # 严重延期
        elif completion_rate < 80:
            return 7  # 中度延期
        else:
            return 3  # 轻微延期
    else:
        # 计算时间进度百分比
        total_days = get_days_difference(create_date, due_date)
        elapsed_days = get_days_difference(create_date, today)

        # 防止除零
        if total_days <= 0:
            time_percentage = 100
        else:
            time_percentage = (elapsed_days / total_days) * 100

        # 比较时间进度和完成率
        if time_percentage > completion_rate + 15:
            # 时间进度远超完成率，需要延期
            return int((time_percentage - completion_rate) / 10)
        elif time_percentage < completion_rate - 30:
            # 完成率远超时间进度，可以提前
            return -int((completion_rate - time_percentage) / 15)

    # 根据风险等级调整
    if risk_level == "HIGH":
        return 5
    elif risk_level == "MEDIUM":
        return 2

    return 0
