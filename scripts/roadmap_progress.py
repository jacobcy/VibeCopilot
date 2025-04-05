#!/usr/bin/env python3
"""
CDDRG路线图进度报告生成器。

用于生成CDDRG引擎库路线图的进度报告。
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

import yaml


def load_yaml(yaml_path: str) -> Dict[str, Any]:
    """加载YAML文件内容。"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_progress_report(roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成路线图进度报告。"""
    milestones = roadmap_data.get("milestones", [])
    tasks = roadmap_data.get("tasks", [])

    # 初始化报告数据
    report = {
        "title": roadmap_data.get("title", "未命名路线图"),
        "description": roadmap_data.get("description", ""),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_progress": 0,
        "milestones": [],
        "tasks_summary": {
            "total": len(tasks),
            "completed": 0,
            "in_progress": 0,
            "todo": 0,
            "planned": 0,
            "by_priority": defaultdict(int),
        },
    }

    # 处理里程碑
    total_progress = 0
    for milestone in milestones:
        milestone_id = milestone.get("id")
        milestone_tasks = [t for t in tasks if t.get("milestone") == milestone_id]

        completed = len([t for t in milestone_tasks if t.get("status") == "completed"])
        in_progress = len([t for t in milestone_tasks if t.get("status") == "in_progress"])
        todo = len([t for t in milestone_tasks if t.get("status") == "todo"])
        planned = len([t for t in milestone_tasks if t.get("status") == "planned"])

        milestone_report = {
            "id": milestone_id,
            "name": milestone.get("name"),
            "status": milestone.get("status"),
            "progress": milestone.get("progress", 0),
            "tasks": {
                "total": len(milestone_tasks),
                "completed": completed,
                "in_progress": in_progress,
                "todo": todo,
                "planned": planned,
            },
        }

        report["milestones"].append(milestone_report)
        total_progress += milestone.get("progress", 0)

    # 计算总体进度
    if milestones:
        report["overall_progress"] = total_progress / len(milestones)

    # 处理任务
    for task in tasks:
        status = task.get("status")
        priority = task.get("priority")

        if status == "completed":
            report["tasks_summary"]["completed"] += 1
        elif status == "in_progress":
            report["tasks_summary"]["in_progress"] += 1
        elif status == "todo":
            report["tasks_summary"]["todo"] += 1
        elif status == "planned":
            report["tasks_summary"]["planned"] += 1

        report["tasks_summary"]["by_priority"][priority] += 1

    return report


def generate_markdown_report(report: Dict[str, Any]) -> str:
    """生成Markdown格式的进度报告。"""
    md = f"# {report['title']} - 进度报告\n\n"
    md += f"*生成时间: {report['generated_at']}*\n\n"
    md += f"## 项目概述\n\n{report['description']}\n\n"
    md += f"## 总体进度: {report['overall_progress']:.1f}%\n\n"

    md += "## 里程碑进度\n\n"
    md += "| 里程碑 | 状态 | 进度 | 任务总数 | 已完成 | 进行中 | 待办 | 规划中 |\n"
    md += "|-------|------|------|----------|--------|--------|------|--------|\n"

    for milestone in report["milestones"]:
        tasks = milestone["tasks"]
        md += f"| {milestone['name']} | {milestone['status']} | {milestone['progress']}% | "
        md += f"{tasks['total']} | {tasks['completed']} | {tasks['in_progress']} | {tasks['todo']} | {tasks['planned']} |\n"

    md += "\n## 任务统计\n\n"
    tasks_summary = report["tasks_summary"]
    md += f"- **总任务数**: {tasks_summary['total']}\n"
    md += f"- **已完成**: {tasks_summary['completed']}\n"
    md += f"- **进行中**: {tasks_summary['in_progress']}\n"
    md += f"- **待办**: {tasks_summary['todo']}\n"
    md += f"- **规划中**: {tasks_summary['planned']}\n\n"

    md += "### 按优先级分布\n\n"
    md += "| 优先级 | 任务数 |\n"
    md += "|--------|-------|\n"

    for priority, count in sorted(tasks_summary["by_priority"].items()):
        md += f"| {priority} | {count} |\n"

    return md


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(description="生成CDDRG路线图进度报告")
    parser.add_argument("--roadmap", required=True, help="路线图YAML文件路径")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="输出格式")

    args = parser.parse_args()

    roadmap_data = load_yaml(args.roadmap)
    report = generate_progress_report(roadmap_data)

    if args.format == "markdown":
        output_content = generate_markdown_report(report)
    else:
        output_content = json.dumps(report, ensure_ascii=False, indent=2)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"进度报告已生成: {args.output}")


if __name__ == "__main__":
    main()
