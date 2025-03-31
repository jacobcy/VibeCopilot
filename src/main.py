#!/usr/bin/env python3
"""
VibeCopilot - AI辅助项目管理工具

主入口文件
"""

import os
import sys
import logging
import argparse
from typing import List, Optional

from src.core.config import get_config
from src.core.state_manager import StateManager, ProjectPhase, TaskStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    os.makedirs(os.path.join(path, ".vibecopilot"), exist_ok=True)
    os.makedirs(os.path.join(path, "docs"), exist_ok=True)

    # 初始化状态管理器（会自动创建初始状态文件）
    state_manager = StateManager(path)

    # 为首个阶段的首个任务设置状态为进行中
    state_manager.set_task_status(
        ProjectPhase.SETUP.value,
        "development_tools",
        TaskStatus.IN_PROGRESS
    )

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
    if not os.path.exists(os.path.join(path, ".vibecopilot")):
        logger.error(f"项目未初始化: {path}")
        logger.info("提示: 请运行 'vibecopilot init' 初始化项目")
        return

    # 加载状态
    state_manager = StateManager(path)
    report = state_manager.get_progress_report()

    # 显示项目状态
    print("\n" + "="*50)
    print(f"项目名称: {report['project_name']}")
    print(f"当前阶段: {report['current_phase']}")
    print(f"总体进度: {report['overall_progress']}%")
    print("="*50)

    # 显示各阶段状态
    print("\n阶段状态:")
    for phase_name, phase_data in report['phases'].items():
        status_symbol = "🟢" if phase_data["status"] == TaskStatus.COMPLETED.value else \
                       "🔄" if phase_data["status"] == TaskStatus.IN_PROGRESS.value else "⚪"
        print(f"{status_symbol} {phase_name.capitalize()}: {phase_data['progress']}% " +
              f"({phase_data['completed_tasks']}/{phase_data['task_count']} 任务完成)")

    # 显示当前阶段的任务
    current_phase = report['current_phase']
    tasks = state_manager.get_phase_tasks(current_phase)

    if tasks:
        print(f"\n当前阶段 ({current_phase.capitalize()}) 任务:")

        for task_id, task_data in tasks.items():
            status_symbol = "✅" if task_data["status"] == TaskStatus.COMPLETED.value else \
                           "🔄" if task_data["status"] == TaskStatus.IN_PROGRESS.value else \
                           "❌" if task_data["status"] == TaskStatus.BLOCKED.value else "⏳"

            print(f"  {status_symbol} {task_data['description']} ({task_data['progress']}%)")

    # 显示文档状态
    print("\n文档状态:")
    for doc_type, doc_data in report['documents'].items():
        status_text = {
            "not_created": "未创建",
            "in_progress": "进行中",
            "created": "已创建"
        }.get(doc_data["status"], doc_data["status"])

        status_symbol = "📄" if doc_data["status"] == "created" else \
                       "🔄" if doc_data["status"] == "in_progress" else "❓"

        print(f"  {status_symbol} {doc_type}: {status_text}")

    print("\n提示: 运行 'vibecopilot help' 查看可用命令")

def update_task(project_path: Optional[str] = None, phase: str = None,
                task_id: str = None, status: str = None, progress: int = None) -> bool:
    """
    更新任务状态

    Args:
        project_path: 项目路径
        phase: 阶段名称
        task_id: 任务ID
        status: 新状态
        progress: 新进度

    Returns:
        是否成功
    """
    if not phase or not task_id or not status:
        logger.error("缺少必要参数: phase, task_id, status")
        return False

    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, ".vibecopilot")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 验证阶段和状态
    try:
        phase_enum = ProjectPhase(phase)
    except ValueError:
        logger.error(f"无效的阶段: {phase}")
        logger.info(f"有效的阶段: {[p.value for p in ProjectPhase]}")
        return False

    try:
        status_enum = TaskStatus(status)
    except ValueError:
        logger.error(f"无效的状态: {status}")
        logger.info(f"有效的状态: {[s.value for s in TaskStatus]}")
        return False

    # 更新任务状态
    state_manager = StateManager(path)
    result = state_manager.set_task_status(phase, task_id, status_enum, progress)

    if result:
        logger.info(f"已更新任务 [{phase}] {task_id} 的状态为 {status}")
        if progress is not None:
            logger.info(f"已更新任务进度为 {progress}%")

    return result

def advance_phase(project_path: Optional[str] = None) -> bool:
    """
    推进到下一个项目阶段

    Args:
        project_path: 项目路径

    Returns:
        是否成功
    """
    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, ".vibecopilot")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 推进阶段
    state_manager = StateManager(path)
    current_phase = state_manager.get_current_phase()

    result = state_manager.advance_phase()

    if result:
        new_phase = state_manager.get_current_phase()
        logger.info(f"已从阶段 {current_phase} 推进到 {new_phase}")
    else:
        logger.warning("无法推进到下一阶段")

    return result

def update_document(project_path: Optional[str] = None, doc_type: str = None,
                   status: str = None) -> bool:
    """
    更新文档状态

    Args:
        project_path: 项目路径
        doc_type: 文档类型
        status: 新状态

    Returns:
        是否成功
    """
    if not doc_type or not status:
        logger.error("缺少必要参数: doc_type, status")
        return False

    path = project_path or os.getcwd()

    # 检查项目是否已初始化
    if not os.path.exists(os.path.join(path, ".vibecopilot")):
        logger.error(f"项目未初始化: {path}")
        return False

    # 验证状态
    valid_statuses = ["not_created", "in_progress", "created"]
    if status not in valid_statuses:
        logger.error(f"无效的文档状态: {status}")
        logger.info(f"有效的状态: {valid_statuses}")
        return False

    # 更新文档状态
    state_manager = StateManager(path)
    result = state_manager.update_document_status(doc_type, status)

    if result:
        logger.info(f"已更新文档 {doc_type} 的状态为 {status}")
    else:
        logger.error(f"更新文档状态失败")

    return result

def show_help() -> None:
    """显示帮助信息"""
    print("\nVibeCopilot - AI辅助项目管理工具")
    print("\n可用命令:")
    print("  init                              初始化新项目")
    print("  status                            显示项目状态")
    print("  update-task --phase PHASE --task TASK_ID --status STATUS [--progress PROGRESS]")
    print("                                   更新任务状态")
    print("  advance-phase                     推进到下一个项目阶段")
    print("  update-document --type DOC_TYPE --status STATUS")
    print("                                   更新文档状态")
    print("  help                              显示此帮助信息")
    print("\n示例:")
    print("  vibecopilot init")
    print("  vibecopilot status")
    print("  vibecopilot update-task --phase setup --task development_tools --status completed")
    print("  vibecopilot advance-phase")
    print("  vibecopilot update-document --type prd --status created")

def main(argv: List[str] = None) -> int:
    """
    主函数

    Args:
        argv: 命令行参数

    Returns:
        退出码
    """
    parser = argparse.ArgumentParser(description="VibeCopilot - AI辅助项目管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化新项目")
    init_parser.add_argument("--path", help="项目路径")

    # status 命令
    status_parser = subparsers.add_parser("status", help="显示项目状态")
    status_parser.add_argument("--path", help="项目路径")

    # update-task 命令
    update_task_parser = subparsers.add_parser("update-task", help="更新任务状态")
    update_task_parser.add_argument("--path", help="项目路径")
    update_task_parser.add_argument("--phase", required=True, help="阶段名称")
    update_task_parser.add_argument("--task", required=True, help="任务ID")
    update_task_parser.add_argument("--status", required=True, help="新状态")
    update_task_parser.add_argument("--progress", type=int, help="新进度")

    # advance-phase 命令
    advance_phase_parser = subparsers.add_parser("advance-phase", help="推进到下一个项目阶段")
    advance_phase_parser.add_argument("--path", help="项目路径")

    # update-document 命令
    update_document_parser = subparsers.add_parser("update-document", help="更新文档状态")
    update_document_parser.add_argument("--path", help="项目路径")
    update_document_parser.add_argument("--type", required=True, help="文档类型")
    update_document_parser.add_argument("--status", required=True, help="新状态")

    # help 命令
    subparsers.add_parser("help", help="显示帮助信息")

    # 解析参数
    args = parser.parse_args(argv)

    # 执行命令
    if args.command == "init":
        success = init_project(args.path)
        return 0 if success else 1

    elif args.command == "status":
        show_status(args.path)
        return 0

    elif args.command == "update-task":
        success = update_task(args.path, args.phase, args.task, args.status, args.progress)
        return 0 if success else 1

    elif args.command == "advance-phase":
        success = advance_phase(args.path)
        return 0 if success else 1

    elif args.command == "update-document":
        success = update_document(args.path, args.type, args.status)
        return 0 if success else 1

    elif args.command == "help" or not args.command:
        show_help()
        return 0

    else:
        logger.error(f"未知命令: {args.command}")
        show_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
