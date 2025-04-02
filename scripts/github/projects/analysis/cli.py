#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行接口模块.

提供项目分析和路线图调整的命令行工具。
"""

import argparse
import json
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from .analyzer import ProjectAnalyzer
from .timeline_adjuster import TimelineAdjuster


def setup_logging(verbose: bool = False):
    """设置日志.

    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def parse_args():
    """解析命令行参数."""
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


def load_config():
    """加载配置.

    Returns:
        Dict[str, Any]: 配置项
    """
    # 加载环境变量
    load_dotenv()

    config = {
        "owner": os.getenv("GITHUB_OWNER"),
        "repo": os.getenv("GITHUB_REPO"),
        "project_number": os.getenv("GITHUB_PROJECT_NUMBER"),
    }

    return config


def analyze_project(args, config: Dict[str, Any]):
    """分析项目.

    Args:
        args: 命令行参数
        config: 配置项
    """
    logging.info("开始分析项目")

    # 获取参数，优先使用命令行参数，其次使用配置
    owner = args.owner or config.get("owner")
    repo = args.repo or config.get("repo")
    project_number = args.project_number or config.get("project_number")

    if not all([owner, repo, project_number]):
        logging.error("缺少必要参数: owner, repo, project_number")
        print("错误: 请提供仓库所有者、仓库名称和项目编号")
        return

    # 创建分析器
    analyzer = ProjectAnalyzer()

    # 解析指标列表
    metrics = args.metrics.split(",") if args.metrics else ["progress", "quality", "risks"]

    # 执行分析
    analysis = analyzer.analyze_project(
        owner=owner, repo=repo, project_number=int(project_number), metrics=metrics
    )

    # 生成报告
    if args.format == "markdown":
        report = analyzer.generate_report(analysis, format_type="markdown")

        # 输出报告
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            logging.info(f"已将报告保存到 {args.output}")
        else:
            print(report)
    else:
        # 保存分析结果
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logging.info(f"已将分析结果保存到 {args.output}")


def adjust_timeline(args, config: Dict[str, Any]):
    """调整时间线.

    Args:
        args: 命令行参数
        config: 配置项
    """
    logging.info("开始调整时间线")

    # 获取参数
    owner = args.owner or config.get("owner")
    repo = args.repo or config.get("repo")
    project_number = args.project_number or config.get("project_number")

    if not all([owner, repo, project_number]):
        logging.error("缺少必要参数: owner, repo, project_number")
        print("错误: 请提供仓库所有者、仓库名称和项目编号")
        return

    # 加载分析结果
    try:
        with open(args.based_on_analysis, "r", encoding="utf-8") as f:
            analysis = json.load(f)
    except Exception as e:
        logging.error(f"加载分析文件失败: {str(e)}")
        print(f"错误: 无法加载分析文件 {args.based_on_analysis}")
        return

    # 创建时间线调整器
    adjuster = TimelineAdjuster()

    # 执行调整
    result = adjuster.adjust_timeline(
        owner=owner,
        repo=repo,
        project_number=int(project_number),
        analysis=analysis,
        update_milestones=args.update_milestones,
        max_adjustment_days=args.max_adjustment_days,
    )

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logging.info(f"已将时间线调整结果保存到 {args.output}")

    # 输出摘要
    adjustments = result.get("adjustments", [])
    print(f"时间线调整完成! 共调整了 {len(adjustments)} 个里程碑")

    if adjustments:
        print("\n调整摘要:")
        for adj in adjustments[:5]:  # 只显示前5个
            milestone = adj.get("milestone", "")
            days = adj.get("adjustment_days", 0)
            direction = "延期" if days > 0 else "提前"
            print(f"- {milestone}: {direction} {abs(days)} 天")

        if len(adjustments) > 5:
            print(f"... 以及其他 {len(adjustments) - 5} 个调整")


def apply_updates(args, config: Dict[str, Any]):
    """应用更新.

    Args:
        args: 命令行参数
        config: 配置项
    """
    logging.info(f"开始应用更新 (dry_run={args.dry_run})")

    # 获取参数
    owner = args.owner or config.get("owner")
    repo = args.repo or config.get("repo")

    if not all([owner, repo]):
        logging.error("缺少必要参数: owner, repo")
        print("错误: 请提供仓库所有者和仓库名称")
        return

    # 创建时间线调整器
    adjuster = TimelineAdjuster()

    # 应用更新
    result = adjuster.apply_updates_from_file(
        owner=owner, repo=repo, updates_file=args.updates_file, dry_run=args.dry_run
    )

    # 保存结果
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logging.info(f"已将更新结果保存到 {args.output}")

    # 输出摘要
    success = result.get("success", False)
    stats = result.get("stats", {})
    total = stats.get("total", 0)
    success_count = stats.get("success", 0)
    failed = stats.get("failed", 0)

    status = "成功" if success else "部分失败"
    mode = "模拟" if args.dry_run else "实际"

    print(f"{mode}更新{status}! 总计: {total}, 成功: {success_count}, 失败: {failed}")

    if failed > 0:
        print("\n失败的更新:")
        for fail in result.get("failed_updates", [])[:5]:  # 只显示前5个
            error = fail.get("error", "未知错误")
            data_type = fail.get("type", "未知类型")
            print(f"- {data_type}: {error}")

        failed_count = len(result.get("failed_updates", []))
        if failed_count > 5:
            print(f"... 以及其他 {failed_count - 5} 个失败")


def generate_report(args):
    """生成报告.

    Args:
        args: 命令行参数
    """
    logging.info("开始生成报告")

    # 加载输入文件
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"加载输入文件失败: {str(e)}")
        print(f"错误: 无法加载输入文件 {args.input}")
        return

    # 生成报告
    report = ""

    if "progress" in data:
        # 这是一个分析结果文件
        analyzer = ProjectAnalyzer()
        report = analyzer.generate_report(data, format_type=args.format)
    else:
        # 这可能是一个调整结果文件
        report = generate_adjustment_report(data, args.format)

    # 输出报告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        logging.info(f"已将报告保存到 {args.output}")
    else:
        print(report)


def generate_adjustment_report(data: Dict[str, Any], format_type: str) -> str:
    """生成调整报告.

    Args:
        data: 调整数据
        format_type: 报告格式

    Returns:
        str: 格式化的报告
    """
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)

    # Markdown或文本格式
    lines = ["# 路线图更新报告", ""]

    # 添加日期
    if "date" in data:
        lines.append(f"生成时间: {data['date']}")
        lines.append("")

    # 添加调整摘要
    adjustments = data.get("adjustments", [])
    lines.append(f"## 更新摘要")
    lines.append("")
    lines.append(f"- 调整了 {len(adjustments)} 个里程碑的时间线")

    if "stats" in data:
        stats = data["stats"]
        lines.append(f"- 总计操作: {stats.get('total', 0)}")
        lines.append(f"- 成功操作: {stats.get('success', 0)}")
        lines.append(f"- 失败操作: {stats.get('failed', 0)}")

    # 添加详细调整
    if adjustments:
        lines.append("")
        lines.append("## 调整详情")
        lines.append("")

        if format_type == "markdown":
            lines.append("| 里程碑 | 调整 | 原截止日期 | 新截止日期 |")
            lines.append("| ------ | ---- | ---------- | ---------- |")

            for adj in adjustments:
                milestone = adj.get("milestone", "未知里程碑")
                days = adj.get("adjustment_days", 0)
                direction = "延期" if days > 0 else "提前"
                old_date = adj.get("original_due_date", "未知")
                new_date = adj.get("new_due_date", "未知")

                lines.append(
                    f"| {milestone} | {direction} {abs(days)} 天 | {old_date} | {new_date} |"
                )
        else:
            for adj in adjustments:
                milestone = adj.get("milestone", "未知里程碑")
                days = adj.get("adjustment_days", 0)
                direction = "延期" if days > 0 else "提前"
                old_date = adj.get("original_due_date", "未知")
                new_date = adj.get("new_due_date", "未知")

                lines.append(f"- {milestone}: {direction} {abs(days)} 天 ({old_date} -> {new_date})")

    # 添加失败的操作
    failed_updates = data.get("failed_updates", [])
    if failed_updates:
        lines.append("")
        lines.append("## 失败的操作")
        lines.append("")

        for fail in failed_updates:
            error = fail.get("error", "未知错误")
            data_type = fail.get("type", "未知类型")
            data_info = fail.get("data", {})

            if format_type == "markdown":
                lines.append(f"- **{data_type}**: {error}")
                lines.append(f"  - 详情: `{json.dumps(data_info)}`")
            else:
                lines.append(f"- {data_type}: {error}")
                lines.append(f"  详情: {data_info}")

    return "\n".join(lines)


def main():
    """主函数."""
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 加载配置
    config = load_config()

    # 执行命令
    if args.command == "analyze":
        analyze_project(args, config)
    elif args.command == "adjust":
        adjust_timeline(args, config)
    elif args.command == "apply":
        apply_updates(args, config)
    elif args.command == "report":
        generate_report(args)
    else:
        print("请指定子命令: analyze, adjust, apply, report")
        print("使用 --help 查看帮助")


if __name__ == "__main__":
    main()
