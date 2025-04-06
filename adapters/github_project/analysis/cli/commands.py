#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令处理模块.

提供各种命令的执行逻辑，处理分析、调整、应用和报告生成。
"""

import json
import logging
from typing import Any, Dict, List

from ..analyzer import ProjectAnalyzer
from ..timeline_adjuster import TimelineAdjuster


def analyze_project(args, config: Dict[str, Any]):
    """分析项目.

    根据命令行参数和配置执行项目分析，生成分析报告。

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

    根据命令行参数和配置执行时间线调整，生成调整结果。

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

    根据命令行参数和配置应用更新，可选择模拟执行或实际执行。

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
