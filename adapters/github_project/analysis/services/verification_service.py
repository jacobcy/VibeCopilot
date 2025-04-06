#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证服务模块.

验证时间线调整的结果.
"""

import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from ....github.api import GitHubClient
from ..utils import format_date, parse_date


def verify_updates(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    updates_file: str,
    generate_diff: bool = True,
) -> Dict[str, Any]:
    """验证更新结果.

    Args:
        github_client: GitHub API客户端
        owner: 仓库所有者
        repo: 仓库名称
        updates_file: 更新文件路径
        generate_diff: 是否生成差异报告

    Returns:
        Dict[str, Any]: 验证结果
    """
    logger = logging.getLogger(__name__)

    try:
        with open(updates_file, "r", encoding="utf-8") as f:
            updates = json.load(f)
    except Exception as e:
        logger.error(f"读取更新文件失败: {str(e)}")
        return {"success": False, "error": str(e)}

    verification_results = {
        "success": True,
        "verified_updates": [],
        "failed_verifications": [],
        "diff": {},
    }

    # 验证时间线调整
    timeline_adjustments = updates.get("timeline_adjustments", [])
    for adjustment in timeline_adjustments:
        try:
            milestone_number = adjustment.get("milestone_number")
            if not milestone_number:
                logger.warning(f"跳过未指定里程碑编号的验证: {adjustment}")
                continue

            expected_due_date = adjustment.get("new_due_date")
            if not expected_due_date:
                logger.warning(f"跳过未指定期望截止日期的验证: {adjustment}")
                continue

            # 获取当前里程碑状态
            try:
                milestone_data = github_client.get(
                    f"repos/{owner}/{repo}/milestones/{milestone_number}"
                )

                if not milestone_data:
                    logger.error(f"无法获取里程碑 #{milestone_number} 数据")
                    verification_results["failed_verifications"].append(
                        {
                            "type": "timeline_adjustment",
                            "data": adjustment,
                            "error": f"无法获取里程碑 #{milestone_number} 数据",
                        }
                    )
                    continue

                # 获取实际截止日期
                actual_due_date = milestone_data.get("due_on")
                if not actual_due_date:
                    logger.error(f"里程碑 #{milestone_number} 没有截止日期")
                    verification_results["failed_verifications"].append(
                        {
                            "type": "timeline_adjustment",
                            "data": adjustment,
                            "error": "里程碑没有截止日期",
                        }
                    )
                    continue

                # 标准化日期格式进行比较
                expected_date_obj = parse_date(expected_due_date)
                actual_date_obj = parse_date(actual_due_date)

                expected_date_str = format_date(expected_date_obj)
                actual_date_str = format_date(actual_date_obj)

                # 比较日期
                if expected_date_str == actual_date_str:
                    logger.info(f"里程碑 #{milestone_number} 验证成功")
                    verification_results["verified_updates"].append(
                        {
                            "type": "timeline_adjustment",
                            "data": adjustment,
                            "actual": actual_date_str,
                        }
                    )
                else:
                    logger.warning(
                        f"里程碑 #{milestone_number} 日期不匹配: "
                        f"期望={expected_date_str}, 实际={actual_date_str}"
                    )
                    verification_results["failed_verifications"].append(
                        {
                            "type": "timeline_adjustment",
                            "data": adjustment,
                            "expected": expected_date_str,
                            "actual": actual_date_str,
                            "error": "日期不匹配",
                        }
                    )

                    # 生成差异
                    if generate_diff:
                        if "milestones" not in verification_results["diff"]:
                            verification_results["diff"]["milestones"] = {}

                        verification_results["diff"]["milestones"][milestone_number] = {
                            "title": milestone_data.get("title", f"里程碑 #{milestone_number}"),
                            "expected": expected_date_str,
                            "actual": actual_date_str,
                        }
            except Exception as e:
                logger.error(f"验证里程碑 #{milestone_number} 时出错: {str(e)}")
                verification_results["failed_verifications"].append(
                    {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
                )
        except Exception as e:
            logger.error(f"处理时间线调整验证时出错: {str(e)}")
            verification_results["failed_verifications"].append(
                {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
            )

    # 更新结果统计
    verification_results["stats"] = {
        "total": len(timeline_adjustments),
        "success": len(verification_results["verified_updates"]),
        "failed": len(verification_results["failed_verifications"]),
    }

    if verification_results["failed_verifications"]:
        verification_results["success"] = False

    return verification_results
