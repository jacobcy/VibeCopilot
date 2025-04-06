#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
参数解析模块.

提供命令行参数解析功能，用于处理各种子命令和参数。
"""

import argparse


def parse_args():
    """解析命令行参数.

    Returns:
        argparse.Namespace: 解析后的参数对象
    """
    parser = argparse.ArgumentParser(description="GitHub项目分析和路线图调整工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 项目分析命令
    analyze_parser = subparsers.add_parser("analyze", help="分析项目状态")
    analyze_parser.add_argument("--owner", help="仓库所有者")
    analyze_parser.add_argument("--repo", help="仓库名称")
    analyze_parser.add_argument("--project-number", type=int, help="项目编号")
    analyze_parser.add_argument("--metrics", default="progress,quality,risks", help="要分析的指标,用逗号分隔")
    analyze_parser.add_argument("--output", default="analysis.json", help="分析结果输出文件")
    analyze_parser.add_argument(
        "--format", default="json", choices=["json", "markdown"], help="输出格式"
    )
    analyze_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    # 调整时间线命令
    adjust_parser = subparsers.add_parser("adjust", help="调整项目时间线")
    adjust_parser.add_argument("--owner", help="仓库所有者")
    adjust_parser.add_argument("--repo", help="仓库名称")
    adjust_parser.add_argument("--project-number", type=int, help="项目编号")
    adjust_parser.add_argument("--based-on-analysis", default="analysis.json", help="分析结果文件路径")
    adjust_parser.add_argument("--update-milestones", default=True, type=bool, help="是否更新里程碑日期")
    adjust_parser.add_argument("--max-adjustment-days", default=30, type=int, help="最大调整天数")
    adjust_parser.add_argument("--output", default="timeline_adjustments.json", help="调整结果输出文件")
    adjust_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    # 应用更新命令
    apply_parser = subparsers.add_parser("apply", help="应用更新")
    apply_parser.add_argument("--owner", help="仓库所有者")
    apply_parser.add_argument("--repo", help="仓库名称")
    apply_parser.add_argument("--updates-file", required=True, help="更新文件路径")
    apply_parser.add_argument("--dry-run", default=True, type=bool, help="是否仅模拟执行")
    apply_parser.add_argument("--output", default="update_results.json", help="更新结果输出文件")
    apply_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    # 生成报告命令
    report_parser = subparsers.add_parser("report", help="生成报告")
    report_parser.add_argument("--input", required=True, help="输入文件路径（分析结果或调整结果）")
    report_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json", "text"], help="报告格式"
    )
    report_parser.add_argument("--output", help="报告输出文件路径")
    report_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    return parser.parse_args()
