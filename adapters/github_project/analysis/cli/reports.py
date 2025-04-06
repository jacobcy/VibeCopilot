#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告生成模块.

提供各种格式的报告生成和处理功能，包括调整报告和分析报告。
"""

import json
import logging
from typing import Any, Dict

from ..analyzer import ProjectAnalyzer


def generate_report(args):
    """生成报告.

    根据命令行参数加载输入文件并生成相应格式的报告。

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

    根据调整数据生成特定格式的报告。

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
