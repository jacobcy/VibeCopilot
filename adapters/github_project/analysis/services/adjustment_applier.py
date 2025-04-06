#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调整应用模块.

应用计算好的时间线调整到GitHub项目。
"""

import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from ....github.api import GitHubClient
from ..utils import format_date, parse_date


def apply_adjustments(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    adjustments: Dict[str, Dict[str, Any]],
    update_milestones: bool,
) -> List[Dict[str, Any]]:
    """应用时间线调整.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称
        adjustments: 调整计划
        update_milestones: 是否实际更新里程碑

    Returns:
        List[Dict[str, Any]]: 已应用的调整
    """
    logger = logging.getLogger(__name__)
    logger.info(f"应用时间线调整 (update_milestones={update_milestones})")

    if not adjustments:
        logger.info("没有需要调整的时间线")
        return []

    applied_adjustments = []

    for milestone_title, adjustment in adjustments.items():
        milestone = adjustment["milestone"]
        new_due_date = adjustment["new_due_date"]
        adjustment_days = adjustment["adjustment_days"]

        # 显示调整信息
        direction = "延期" if adjustment_days > 0 else "提前"
        days = abs(adjustment_days)

        logger.info(f"里程碑 '{milestone_title}' {direction} {days} 天")

        # 如果需要更新里程碑
        if update_milestones:
            try:
                # 更新里程碑截止日期
                milestone_number = milestone["number"]

                # 格式化日期为ISO 8601格式
                new_due_date_str = format_date(new_due_date, "%Y-%m-%dT%H:%M:%SZ")

                # 调用API更新里程碑
                github_client.patch(
                    f"repos/{owner}/{repo}/milestones/{milestone_number}",
                    json={"due_on": new_due_date_str},
                )

                logger.info(f"已更新里程碑 '{milestone_title}' 的截止日期")

                # 记录已应用的调整
                applied_adjustments.append(
                    {
                        "milestone": milestone_title,
                        "milestone_number": milestone_number,
                        "adjustment_days": adjustment_days,
                        "new_due_date": format_date(new_due_date),
                        "original_due_date": format_date(adjustment["original_due_date"]),
                    }
                )
            except Exception as e:
                logger.error(f"更新里程碑 '{milestone_title}' 失败: {str(e)}")
        else:
            # 模拟调整（不实际更新）
            applied_adjustments.append(
                {
                    "milestone": milestone_title,
                    "milestone_number": milestone.get("number"),
                    "adjustment_days": adjustment_days,
                    "new_due_date": format_date(new_due_date),
                    "original_due_date": format_date(adjustment["original_due_date"]),
                    "simulated": True,
                }
            )

    return applied_adjustments


def apply_updates(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    updates: Dict[str, Any],
    dry_run: bool = True,
) -> Dict[str, Any]:
    """应用更新.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称
        updates: 更新数据
        dry_run: 是否仅模拟执行

    Returns:
        Dict[str, Any]: 应用结果
    """
    logger = logging.getLogger(__name__)
    results = {
        "success": True,
        "date": datetime.datetime.now().isoformat(),
        "applied_updates": [],
        "failed_updates": [],
    }

    # 处理时间线调整
    timeline_adjustments = updates.get("timeline_adjustments", [])
    for adjustment in timeline_adjustments:
        try:
            milestone_number = adjustment.get("milestone_number")
            if not milestone_number:
                logger.warning(f"跳过未指定里程碑编号的调整: {adjustment}")
                continue

            new_due_date = adjustment.get("new_due_date")
            if not new_due_date:
                logger.warning(f"跳过未指定新截止日期的调整: {adjustment}")
                continue

            # 转换日期格式
            try:
                due_date_obj = parse_date(new_due_date)
                new_due_date_str = format_date(due_date_obj, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                logger.error(f"无法解析日期格式: {new_due_date}")
                results["failed_updates"].append(
                    {
                        "type": "timeline_adjustment",
                        "data": adjustment,
                        "error": f"无法解析日期格式: {new_due_date}",
                    }
                )
                continue

            if not dry_run:
                # 调用API更新里程碑
                try:
                    github_client.patch(
                        f"repos/{owner}/{repo}/milestones/{milestone_number}",
                        json={"due_on": new_due_date_str},
                    )
                    logger.info(f"已更新里程碑 #{milestone_number} 的截止日期")
                    results["applied_updates"].append(
                        {"type": "timeline_adjustment", "data": adjustment}
                    )
                except Exception as e:
                    logger.error(f"更新里程碑 #{milestone_number} 失败: {str(e)}")
                    results["failed_updates"].append(
                        {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
                    )
            else:
                # 仅记录模拟更新
                logger.info(f"[DRY RUN] 将更新里程碑 #{milestone_number} 的截止日期为 {new_due_date_str}")
                results["applied_updates"].append(
                    {"type": "timeline_adjustment", "data": adjustment, "simulated": True}
                )
        except Exception as e:
            logger.error(f"处理时间线调整时出错: {str(e)}")
            results["failed_updates"].append(
                {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
            )

    # 处理状态更新
    status_changes = updates.get("status_changes", [])
    _apply_status_changes(github_client, owner, repo, status_changes, dry_run, results)

    # 更新结果统计
    results["stats"] = {
        "total": len(timeline_adjustments) + len(status_changes),
        "success": len(results["applied_updates"]),
        "failed": len(results["failed_updates"]),
    }

    if results["failed_updates"]:
        results["success"] = False

    return results


def apply_updates_from_file(
    github_client: GitHubClient, owner: str, repo: str, updates_file: str, dry_run: bool = True
) -> Dict[str, Any]:
    """从文件中应用更新.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称
        updates_file: 更新文件路径
        dry_run: 是否仅模拟执行

    Returns:
        Dict[str, Any]: 应用结果
    """
    logger = logging.getLogger(__name__)

    try:
        with open(updates_file, "r", encoding="utf-8") as f:
            updates = json.load(f)
    except Exception as e:
        logger.error(f"读取更新文件失败: {str(e)}")
        return {"success": False, "error": str(e)}

    return apply_updates(github_client, owner, repo, updates, dry_run)


def _apply_status_changes(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    status_changes: List[Dict[str, Any]],
    dry_run: bool,
    results: Dict[str, Any],
) -> None:
    """应用状态更新.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称
        status_changes: 状态更新列表
        dry_run: 是否仅模拟执行
        results: 结果字典，将被修改
    """
    logger = logging.getLogger(__name__)

    for status_change in status_changes:
        try:
            issue_number = status_change.get("issue_number")
            if not issue_number:
                logger.warning(f"跳过未指定Issue编号的状态更新: {status_change}")
                continue

            new_status = status_change.get("new_status")
            if not new_status:
                logger.warning(f"跳过未指定新状态的更新: {status_change}")
                continue

            if not dry_run:
                # 更新Issue状态
                # 注意：标准GitHub Issues API不直接支持更改状态字段
                # 这里假设状态对应于issue state (open/closed)
                state = "closed" if new_status.lower() in ["closed", "done", "完成"] else "open"

                try:
                    github_client.patch(
                        f"repos/{owner}/{repo}/issues/{issue_number}", json={"state": state}
                    )
                    logger.info(f"已更新Issue #{issue_number} 的状态为 {state}")
                    results["applied_updates"].append(
                        {"type": "status_change", "data": status_change}
                    )
                except Exception as e:
                    logger.error(f"更新Issue #{issue_number} 失败: {str(e)}")
                    results["failed_updates"].append(
                        {"type": "status_change", "data": status_change, "error": str(e)}
                    )
            else:
                # 仅记录模拟更新
                logger.info(f"[DRY RUN] 将更新Issue #{issue_number} 的状态为相应的状态")
                results["applied_updates"].append(
                    {"type": "status_change", "data": status_change, "simulated": True}
                )
        except Exception as e:
            logger.error(f"处理状态更新时出错: {str(e)}")
            results["failed_updates"].append(
                {"type": "status_change", "data": status_change, "error": str(e)}
            )
