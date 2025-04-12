#!/usr/bin/env python3
"""
VibeCopilot - 项目工具函数模块

提供项目初始化、状态显示等项目管理核心功能
"""

import logging
import os
from typing import Optional

from rich.console import Console

from src.core.state_manager import ProjectPhase, StateManager, TaskStatus

# 配置日志
logger = logging.getLogger(__name__)
console = Console()


def init_project(project_path: Optional[str] = None) -> bool:
    """
    初始化新项目

    Args:
        project_path: 项目路径，如果为None则使用当前目录

    Returns:
        是否成功
    """
    path = project_path or os.getcwd()
    logger.info(f"初始化项目: {path}")

    # 创建项目目录结构
    os.makedirs(os.path.join(path, "data/temp"), exist_ok=True)
    os.makedirs(os.path.join(path, "docs"), exist_ok=True)

    # 初始化状态管理器（会自动创建初始状态文件）
    state_manager = StateManager(path)

    # 为首个阶段的首个任务设置状态为进行中
    state_manager.set_task_status(ProjectPhase.SETUP.value, "development_tools", TaskStatus.IN_PROGRESS)

    logger.info(f"项目初始化完成: {path}")
    logger.info("提示: 请运行 'vibecopilot status' 查看项目状态")

    return True


def show_status(project_path: Optional[str] = None) -> None:
    """
    显示项目状态

    Args:
        project_path: 项目路径，如果为None则使用当前目录
    """
    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, "data/temp")):
        logger.error(f"项目未初始化: {path}")
        logger.info("提示: 请运行 'vibecopilot init' 初始化项目")
        return

    # 加载状态
    state_manager = StateManager(path)
    report = state_manager.get_progress_report()

    # 显示项目状态
    print("\n" + "=" * 50)
    print(f"项目名称: {report['project_name']}")
    print(f"当前阶段: {report['current_phase']}")
    print(f"总体进度: {report['overall_progress']}%")
    print("=" * 50)

    # 显示各阶段状态
    print("\n阶段状态:")
    for phase_name, phase_data in report["phases"].items():
        status_symbol = (
            "🟢" if phase_data["status"] == TaskStatus.COMPLETED.value else "🔄" if phase_data["status"] == TaskStatus.IN_PROGRESS.value else "⚪"
        )
        print(
            f"{status_symbol} {phase_name.capitalize()}: {phase_data['progress']}% "
            + f"({phase_data['completed_tasks']}/{phase_data['task_count']} 任务完成)"
        )

    # 显示当前阶段的任务
    current_phase = report["current_phase"]
    tasks = state_manager.get_phase_tasks(current_phase)

    if tasks:
        print(f"\n当前阶段 ({current_phase.capitalize()}) 任务:")

        for task_id, task_data in tasks.items():
            status_symbol = (
                "✅"
                if task_data["status"] == TaskStatus.COMPLETED.value
                else "🔄"
                if task_data["status"] == TaskStatus.IN_PROGRESS.value
                else "❌"
                if task_data["status"] == TaskStatus.BLOCKED.value
                else "⏳"
            )

            print(f"  {status_symbol} {task_data['description']} ({task_data['progress']}%)")

    # 显示文档状态
    print("\n文档状态:")
    for doc_type, doc_data in report["documents"].items():
        status_text = {"not_created": "未创建", "in_progress": "进行中", "created": "已创建"}.get(doc_data["status"], doc_data["status"])

        status_symbol = "📄" if doc_data["status"] == "created" else "🔄" if doc_data["status"] == "in_progress" else "❓"

        print(f"  {status_symbol} {doc_type}: {status_text}")

    print("\n提示: 运行 'vibecopilot help' 查看可用命令")
