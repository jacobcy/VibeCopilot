#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
质量分析模块.

分析GitHub项目的代码质量和审核情况。
"""

from typing import Any, Dict, List


def analyze_quality(project_data: Dict[str, Any]) -> Dict[str, Any]:
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
    pr_merge_rate = round((merged_prs / total_closed_prs) * 100, 2) if total_closed_prs > 0 else 0

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
