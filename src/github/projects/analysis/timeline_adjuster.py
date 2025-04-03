#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间线调整模块.

基于项目分析结果自动调整项目时间线。
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from ...github.api import GitHubClient, GitHubIssuesClient, GitHubProjectsClient


class TimelineAdjuster:
    """项目时间线调整器."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        projects_client: Optional[GitHubProjectsClient] = None,
        issues_client: Optional[GitHubIssuesClient] = None,
    ):
        """初始化时间线调整器.

        Args:
            github_client: GitHub API客户端
            projects_client: GitHub Projects API客户端
            issues_client: GitHub Issues API客户端
        """
        self.github_client = github_client or GitHubClient()
        self.projects_client = projects_client or GitHubProjectsClient()
        self.issues_client = issues_client or GitHubIssuesClient()
        self.logger = logging.getLogger(__name__)

    def adjust_timeline(
        self,
        owner: str,
        repo: str,
        project_number: int,
        analysis: Dict[str, Any],
        update_milestones: bool = True,
        max_adjustment_days: int = 30,
    ) -> Dict[str, Any]:
        """调整项目时间线.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            analysis: 项目分析结果
            update_milestones: 是否更新里程碑
            max_adjustment_days: 最大调整天数限制

        Returns:
            Dict[str, Any]: 调整结果
        """
        # 获取仓库数据
        repo_data = self._get_repo_data(owner, repo)

        # 计算时间线调整
        adjustments = self._calculate_adjustments(analysis, repo_data, max_adjustment_days)

        # 应用调整
        applied_adjustments = self._apply_adjustments(owner, repo, adjustments, update_milestones)

        return {"date": datetime.datetime.now().isoformat(), "adjustments": applied_adjustments}

    def _get_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库数据.

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Dict[str, Any]: 仓库数据
        """
        self.logger.info(f"获取仓库 {owner}/{repo} 数据")

        try:
            # 获取仓库
            repository = self.github_client.get(f"repos/{owner}/{repo}")

            # 获取里程碑
            milestones = self.github_client.get(
                f"repos/{owner}/{repo}/milestones", params={"state": "all"}
            )
            if not isinstance(milestones, list):
                milestones = []

            return {"repository": repository, "milestones": milestones}
        except Exception as e:
            self.logger.error(f"获取仓库数据失败: {str(e)}")
            return {"repository": {}, "milestones": []}

    def _calculate_adjustments(
        self, analysis: Dict[str, Any], repo_data: Dict[str, Any], max_days: int
    ) -> Dict[str, Dict[str, Any]]:
        """计算时间线调整.

        Args:
            analysis: 项目分析结果
            repo_data: 仓库数据
            max_days: 最大调整天数

        Returns:
            Dict[str, Dict[str, Any]]: 调整计划
        """
        self.logger.info("计算时间线调整")

        adjustments = {}

        # 如果没有进度或风险数据，则无法进行调整
        if "progress" not in analysis or "risks" not in analysis:
            self.logger.warning("分析结果中缺少进度或风险数据，无法进行调整")
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
            adjustment_days = self._calculate_adjustment_days(milestone, progress_data, risk_level)

            # 限制最大调整天数
            if adjustment_days > max_days:
                adjustment_days = max_days
            elif adjustment_days < -max_days // 3:  # 提前调整天数限制更严格
                adjustment_days = -max_days // 3

            # 记录调整
            if adjustment_days != 0:
                # 解析日期
                try:
                    due_date = self._parse_date(milestone["due_on"])
                    new_due_date = due_date + datetime.timedelta(days=adjustment_days)

                    adjustments[milestone_title] = {
                        "milestone": milestone,
                        "original_due_date": due_date,
                        "adjustment_days": adjustment_days,
                        "new_due_date": new_due_date,
                    }
                except Exception as e:
                    self.logger.error(f"处理里程碑 '{milestone_title}' 日期时出错: {str(e)}")

        return adjustments

    def _calculate_adjustment_days(
        self, milestone: Dict[str, Any], progress_data: Dict[str, Any], risk_level: str
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
            due_date = self._parse_date(milestone["due_on"])
            create_date = self._parse_date(milestone.get("created_at", ""))
            today = datetime.datetime.now(datetime.timezone.utc)
        except Exception:
            return 0

        # 如果里程碑已过期，设置延期
        if due_date < today:
            # 根据完成率决定延期时间
            if completion_rate < 50:
                return 14  # 严重延期
            elif completion_rate < 80:
                return 7  # 中度延期
            else:
                return 3  # 轻微延期
        else:
            # 计算时间进度百分比
            total_days = (due_date - create_date).days
            elapsed_days = (today - create_date).days

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

    def _apply_adjustments(
        self, owner: str, repo: str, adjustments: Dict[str, Dict[str, Any]], update_milestones: bool
    ) -> List[Dict[str, Any]]:
        """应用时间线调整.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            adjustments: 调整计划
            update_milestones: 是否实际更新里程碑

        Returns:
            List[Dict[str, Any]]: 已应用的调整
        """
        self.logger.info(f"应用时间线调整 (update_milestones={update_milestones})")

        if not adjustments:
            self.logger.info("没有需要调整的时间线")
            return []

        applied_adjustments = []

        for milestone_title, adjustment in adjustments.items():
            milestone = adjustment["milestone"]
            new_due_date = adjustment["new_due_date"]
            adjustment_days = adjustment["adjustment_days"]

            # 显示调整信息
            direction = "延期" if adjustment_days > 0 else "提前"
            days = abs(adjustment_days)

            self.logger.info(f"里程碑 '{milestone_title}' {direction} {days} 天")

            # 如果需要更新里程碑
            if update_milestones:
                try:
                    # 更新里程碑截止日期
                    milestone_number = milestone["number"]

                    # 格式化日期为ISO 8601格式
                    new_due_date_str = new_due_date.strftime("%Y-%m-%dT%H:%M:%SZ")

                    # 调用API更新里程碑
                    self.github_client.patch(
                        f"repos/{owner}/{repo}/milestones/{milestone_number}",
                        json={"due_on": new_due_date_str},
                    )

                    self.logger.info(f"已更新里程碑 '{milestone_title}' 的截止日期")

                    # 记录已应用的调整
                    applied_adjustments.append(
                        {
                            "milestone": milestone_title,
                            "milestone_number": milestone_number,
                            "adjustment_days": adjustment_days,
                            "new_due_date": new_due_date.strftime("%Y-%m-%d"),
                            "original_due_date": adjustment["original_due_date"].strftime(
                                "%Y-%m-%d"
                            ),
                        }
                    )
                except Exception as e:
                    self.logger.error(f"更新里程碑 '{milestone_title}' 失败: {str(e)}")
            else:
                # 模拟调整（不实际更新）
                applied_adjustments.append(
                    {
                        "milestone": milestone_title,
                        "milestone_number": milestone.get("number"),
                        "adjustment_days": adjustment_days,
                        "new_due_date": new_due_date.strftime("%Y-%m-%d"),
                        "original_due_date": adjustment["original_due_date"].strftime("%Y-%m-%d"),
                        "simulated": True,
                    }
                )

        return applied_adjustments

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
            # 尝试其他格式
            try:
                return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=datetime.timezone.utc
                )
            except ValueError:
                # 回退到当前日期
                return datetime.datetime.now(datetime.timezone.utc)

    def apply_updates_from_file(
        self, owner: str, repo: str, updates_file: str, dry_run: bool = True
    ) -> Dict[str, Any]:
        """从文件中应用更新.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates_file: 更新文件路径
            dry_run: 是否仅模拟执行

        Returns:
            Dict[str, Any]: 应用结果
        """
        import json

        try:
            with open(updates_file, "r", encoding="utf-8") as f:
                updates = json.load(f)
        except Exception as e:
            self.logger.error(f"读取更新文件失败: {str(e)}")
            return {"success": False, "error": str(e)}

        return self.apply_updates(owner, repo, updates, dry_run)

    def apply_updates(
        self, owner: str, repo: str, updates: Dict[str, Any], dry_run: bool = True
    ) -> Dict[str, Any]:
        """应用更新.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates: 更新数据
            dry_run: 是否仅模拟执行

        Returns:
            Dict[str, Any]: 应用结果
        """
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
                    self.logger.warning(f"跳过未指定里程碑编号的调整: {adjustment}")
                    continue

                new_due_date = adjustment.get("new_due_date")
                if not new_due_date:
                    self.logger.warning(f"跳过未指定新截止日期的调整: {adjustment}")
                    continue

                # 转换日期格式
                if isinstance(new_due_date, str):
                    # 处理可能的不同日期格式
                    try:
                        due_date_obj = datetime.datetime.fromisoformat(
                            new_due_date.replace("Z", "+00:00")
                        )
                    except ValueError:
                        try:
                            due_date_obj = datetime.datetime.strptime(new_due_date, "%Y-%m-%d")
                        except ValueError:
                            self.logger.error(f"无法解析日期格式: {new_due_date}")
                            results["failed_updates"].append(
                                {
                                    "type": "timeline_adjustment",
                                    "data": adjustment,
                                    "error": f"无法解析日期格式: {new_due_date}",
                                }
                            )
                            continue

                    new_due_date_str = due_date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    self.logger.error(f"日期格式错误: {new_due_date} (应为字符串)")
                    results["failed_updates"].append(
                        {
                            "type": "timeline_adjustment",
                            "data": adjustment,
                            "error": "日期格式错误 (应为字符串)",
                        }
                    )
                    continue

                if not dry_run:
                    # 调用API更新里程碑
                    try:
                        self.github_client.patch(
                            f"repos/{owner}/{repo}/milestones/{milestone_number}",
                            json={"due_on": new_due_date_str},
                        )
                        self.logger.info(f"已更新里程碑 #{milestone_number} 的截止日期")
                        results["applied_updates"].append(
                            {"type": "timeline_adjustment", "data": adjustment}
                        )
                    except Exception as e:
                        self.logger.error(f"更新里程碑 #{milestone_number} 失败: {str(e)}")
                        results["failed_updates"].append(
                            {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
                        )
                else:
                    # 仅记录模拟更新
                    self.logger.info(
                        f"[DRY RUN] 将更新里程碑 #{milestone_number} 的截止日期为 {new_due_date_str}"
                    )
                    results["applied_updates"].append(
                        {"type": "timeline_adjustment", "data": adjustment, "simulated": True}
                    )
            except Exception as e:
                self.logger.error(f"处理时间线调整时出错: {str(e)}")
                results["failed_updates"].append(
                    {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
                )

        # 处理状态更新
        status_changes = updates.get("status_changes", [])
        for status_change in status_changes:
            try:
                issue_number = status_change.get("issue_number")
                if not issue_number:
                    self.logger.warning(f"跳过未指定Issue编号的状态更新: {status_change}")
                    continue

                new_status = status_change.get("new_status")
                if not new_status:
                    self.logger.warning(f"跳过未指定新状态的更新: {status_change}")
                    continue

                if not dry_run:
                    # 更新Issue状态
                    # 注意：标准GitHub Issues API不直接支持更改状态字段
                    # 这里假设状态对应于issue state (open/closed)
                    state = "closed" if new_status.lower() in ["closed", "done", "完成"] else "open"

                    try:
                        self.github_client.patch(
                            f"repos/{owner}/{repo}/issues/{issue_number}", json={"state": state}
                        )
                        self.logger.info(f"已更新Issue #{issue_number} 的状态为 {state}")
                        results["applied_updates"].append(
                            {"type": "status_change", "data": status_change}
                        )
                    except Exception as e:
                        self.logger.error(f"更新Issue #{issue_number} 失败: {str(e)}")
                        results["failed_updates"].append(
                            {"type": "status_change", "data": status_change, "error": str(e)}
                        )
                else:
                    # 仅记录模拟更新
                    self.logger.info(f"[DRY RUN] 将更新Issue #{issue_number} 的状态为相应的状态")
                    results["applied_updates"].append(
                        {"type": "status_change", "data": status_change, "simulated": True}
                    )
            except Exception as e:
                self.logger.error(f"处理状态更新时出错: {str(e)}")
                results["failed_updates"].append(
                    {"type": "status_change", "data": status_change, "error": str(e)}
                )

        # 更新结果统计
        results["stats"] = {
            "total": len(timeline_adjustments) + len(status_changes),
            "success": len(results["applied_updates"]),
            "failed": len(results["failed_updates"]),
        }

        if results["failed_updates"]:
            results["success"] = False

        return results

    def verify_updates(
        self, owner: str, repo: str, updates_file: str, generate_diff: bool = True
    ) -> Dict[str, Any]:
        """验证更新结果.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            updates_file: 更新文件路径
            generate_diff: 是否生成差异报告

        Returns:
            Dict[str, Any]: 验证结果
        """
        import json

        try:
            with open(updates_file, "r", encoding="utf-8") as f:
                updates = json.load(f)
        except Exception as e:
            self.logger.error(f"读取更新文件失败: {str(e)}")
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
                    self.logger.warning(f"跳过未指定里程碑编号的验证: {adjustment}")
                    continue

                expected_due_date = adjustment.get("new_due_date")
                if not expected_due_date:
                    self.logger.warning(f"跳过未指定期望截止日期的验证: {adjustment}")
                    continue

                # 获取当前里程碑状态
                try:
                    milestone_data = self.github_client.get(
                        f"repos/{owner}/{repo}/milestones/{milestone_number}"
                    )

                    if not milestone_data:
                        self.logger.error(f"无法获取里程碑 #{milestone_number} 数据")
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
                        self.logger.error(f"里程碑 #{milestone_number} 没有截止日期")
                        verification_results["failed_verifications"].append(
                            {
                                "type": "timeline_adjustment",
                                "data": adjustment,
                                "error": "里程碑没有截止日期",
                            }
                        )
                        continue

                    # 标准化日期格式进行比较
                    expected_date_obj = self._parse_date(expected_due_date)
                    actual_date_obj = self._parse_date(actual_due_date)

                    expected_date_str = expected_date_obj.strftime("%Y-%m-%d")
                    actual_date_str = actual_date_obj.strftime("%Y-%m-%d")

                    # 比较日期
                    if expected_date_str == actual_date_str:
                        self.logger.info(f"里程碑 #{milestone_number} 验证成功")
                        verification_results["verified_updates"].append(
                            {
                                "type": "timeline_adjustment",
                                "data": adjustment,
                                "actual": actual_date_str,
                            }
                        )
                    else:
                        self.logger.warning(
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
                    self.logger.error(f"验证里程碑 #{milestone_number} 时出错: {str(e)}")
                    verification_results["failed_verifications"].append(
                        {"type": "timeline_adjustment", "data": adjustment, "error": str(e)}
                    )
            except Exception as e:
                self.logger.error(f"处理时间线调整验证时出错: {str(e)}")
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
