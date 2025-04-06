#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告生成器模块.

生成GitHub项目分析报告。
"""

import datetime
import json
from typing import Any, Dict, List

from ..utils import format_date, parse_date


def generate_report(analysis: Dict[str, Any], format_type: str = "markdown") -> str:
    """生成分析报告.

    Args:
        analysis: 分析结果
        format_type: 报告格式类型

    Returns:
        str: 格式化的报告
    """
    if format_type == "markdown":
        return generate_markdown_report(analysis)
    elif format_type == "json":
        return json.dumps(analysis, indent=2)
    else:
        return str(analysis)


def generate_markdown_report(analysis: Dict[str, Any]) -> str:
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
    key_points = extract_key_points(analysis)
    for i, point in enumerate(key_points, 1):
        report.append(f"{i}. {point}")

    # 建议操作
    report.extend(["", "## 建议操作"])
    recommendations = generate_recommendations(analysis)
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


def extract_key_points(analysis: Dict[str, Any]) -> List[str]:
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
                            due_date = parse_date(due_date)
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


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
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
