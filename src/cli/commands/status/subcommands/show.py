"""
状态显示子命令

提供显示项目各种状态信息的命令
"""

import json
import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.commands.status.output_helpers import output_result
from src.core.config import get_config, refresh_config
from src.status.models import StatusSource
from src.status.service import StatusService
from src.utils import console_utils

logger = logging.getLogger(__name__)
console = Console()


def handle_show(service=None, args: Optional[Dict[str, Any]] = None) -> int:
    """处理show子命令

    Args:
        service: 状态服务实例，可选
        args: 命令参数

    Returns:
        int: 命令状态码，0表示成功
    """
    if args is None:
        args = {}

    entity_type = args.get("entity_type")
    entity_id = args.get("entity_id")
    format = args.get("format", "text")
    verbose = args.get("verbose", False)

    try:
        # 如果未提供服务实例，创建一个
        if service is None:
            service = StatusService.get_instance()

        config_manager = get_config()
        app_name = config_manager.get("app.name", "VibeCopilot")

        # 根据参数显示不同的状态
        if entity_type and entity_id:
            # 显示特定实体的状态
            result = service.get_domain_status(entity_type, entity_id)
        elif entity_type:
            # 显示特定领域的状态
            result = service.get_domain_status(entity_type)
        else:
            # 显示系统概览
            result = service.get_system_status(detailed=verbose)

        # 添加应用名称到结果中
        if isinstance(result, dict):
            if "system_info" not in result:
                result["system_info"] = {}
            result["system_info"]["app_name"] = app_name

        # 尝试获取任务摘要
        try:
            task_summary = service.get_domain_status("task")
            if isinstance(task_summary, dict) and "error" not in task_summary:
                result["task_summary"] = task_summary
        except Exception as task_e:
            logger.warning(f"获取任务摘要时出错: {task_e}")

        # 获取 GitHub 信息 - 使用 StatusService
        try:
            github_info_data = service.get_domain_status("github_info")
            if not isinstance(github_info_data, dict):
                github_info_data = {}
                logger.warning("GitHub信息不是字典格式")
        except Exception as e:
            logger.error(f"获取GitHub信息时出错: {e}", exc_info=True)
            github_info_data = {"error": f"获取GitHub信息失败: {str(e)}"}

        # 显示 GitHub 信息
        console.print("\nGitHub 仓库信息:")

        # 显示检测到的仓库
        detected_owner = github_info_data.get("detected_owner")
        detected_repo = github_info_data.get("detected_repo")
        if detected_owner and detected_repo:
            console.print(f"  检测到的仓库: {detected_owner}/{detected_repo}")
        else:
            console.print("  检测到的仓库: 未检测到")

        # 显示配置状态
        if github_info_data.get("configured", False):
            effective_owner = github_info_data.get("effective_owner")
            effective_repo = github_info_data.get("effective_repo")
            console.print(f"  配置的仓库: {effective_owner}/{effective_repo}")
        else:
            console.print("  配置的仓库: 未配置")

        # 显示实际使用的仓库和来源
        effective_owner = github_info_data.get("effective_owner")
        effective_repo = github_info_data.get("effective_repo")
        if effective_owner and effective_repo:
            source = github_info_data.get("source", "未知来源")
            display_source = StatusSource.get_display_name(source)
            console.print(f"  实际使用的仓库: {effective_owner}/{effective_repo} ({display_source})")

            # 显示GitHub链接
            console.print(f"  GitHub链接: https://github.com/{effective_owner}/{effective_repo}")
        else:
            console.print("  实际使用的仓库: 未设置")

        # === 修正: 从 ProjectState 获取活动路线图的 GitHub Project 信息 ===
        project_state_instance = service.project_state  # ProjectState instance
        current_roadmap_id = project_state_instance.get_current_roadmap_id()

        # 优先从 roadmap_github_mapping 获取 GitHub 项目信息
        mapped_node_id = None
        if current_roadmap_id:
            mapped_node_id = project_state_instance.get_github_project_id_for_roadmap(current_roadmap_id)

        # 作为备选，可以查看 active_roadmap_backend_config
        all_backend_configs = project_state_instance.get_active_roadmap_backend_config()
        active_roadmap_gh_config = all_backend_configs.get("github") if isinstance(all_backend_configs, dict) else None

        # 从 active_roadmap_gh_config 或从 GitHub API 获取项目详情
        project_title = None
        project_id = mapped_node_id  # 默认使用 mapping 中的 node_id
        project_number = None

        # 如果 active_roadmap_gh_config 存在，尝试从中获取更多信息
        if active_roadmap_gh_config:
            project_title = active_roadmap_gh_config.get("project_title")
            backend_project_id = active_roadmap_gh_config.get("project_id")
            project_number = active_roadmap_gh_config.get("project_number")

            # 如果 mapping 中的 node_id 与 backend 中的不同，以 mapping 为准，但使用 backend 中的其他信息
            if project_id is None:
                project_id = backend_project_id

        # 如果项目 ID 存在但没有详细信息，尝试从 GitHub 获取
        if project_id and (not project_title or not project_number):
            try:
                # 如果 GitHub 项目同步服务可用，尝试获取详细信息
                if "github_sync" not in locals():
                    from src.sync.github_project import GitHubProjectSync

                    github_sync = GitHubProjectSync()

                # 尝试通过 ID 获取项目详情
                project_detail = github_sync.get_project_by_id(project_id)
                if project_detail and project_detail.get("success") and project_detail.get("project"):
                    project_data = project_detail.get("project")
                    if not project_title:
                        project_title = project_data.get("title")
                    if not project_number:
                        project_number = project_data.get("number")
                    logger.info(f"通过 GitHub API 获取到项目详情: {project_title} (#{project_number})")
            except Exception as e:
                logger.warning(f"尝试获取 GitHub 项目详情时出错: {e}")

        # 显示项目信息
        if project_id:
            if project_title:
                display_project = f"{project_title}"
                if project_number:
                    display_project += f" (#{project_number})"
                console.print(f"  关联的 Project: {display_project}")
                console.print(f"  Project Node ID: {project_id}")
            else:
                console.print(f"  关联的 Project Node ID: {project_id}")
                console.print(f"  [yellow]注意: Project 详细信息 (如标题) 缺失，请尝试同步或切换路线图以更新。[/yellow]")
        else:
            console.print("  关联的 Project: 未配置或未同步")

        # 显示任何错误信息
        if github_info_data.get("error"):
            console.print(f"  警告: [yellow]{github_info_data['error']}[/yellow]")

        # 显示差异信息
        if github_info_data.get("discrepancy_message"):
            console.print(f"  注意: [yellow]{github_info_data['discrepancy_message']}[/yellow]")

        # 输出结果
        if format == "text":
            console.print(f"[bold cyan]=== {app_name} 状态概览 ===[/bold cyan]\n")

            # 手动显示项目状态
            project_state = service.project_state.get_project_state()
            console.print("\n[bold]📊 项目状态:[/bold]")
            console.print(f"  名称: {project_state.get('name', '未设置')}")
            console.print(f"  阶段: {project_state.get('current_phase', '未设置')}")
            try:
                health = service.get_health()
                health_level = health.get("level", 0)
                console.print(f"  健康度: {health_level}%")
                console.print(f"  状态: {health.get('status', '未知')}")
            except Exception as e:
                console.print(f"  健康度: 未知 (错误: {e})")

            # 显示路线图信息
            try:
                roadmap_id = project_state.get("current_roadmap_id")
                if roadmap_id:
                    console.print(f"\n[bold]🗺️ 当前路线图:[/bold]")
                    console.print(f"  ID: {roadmap_id}")

                    # 尝试获取路线图详情
                    try:
                        roadmap_status = service.get_domain_status("roadmap", entity_id=roadmap_id)

                        if isinstance(roadmap_status, dict) and "error" not in roadmap_status:
                            entity_data = roadmap_status.get("entity_data")
                            if isinstance(entity_data, dict):
                                console.print(f"  名称: {entity_data.get('title', '未知')}")  # title 优先于 name
                                console.print(f"  描述: {entity_data.get('description', '无描述')}")
                                console.print(f"  状态: {entity_data.get('status', '未知')}")
                            else:
                                # 如果 entity_data 不是字典，但 roadmap_status 可能直接包含所需信息
                                # 这是一种备用情况，主要期望 entity_data 包含数据
                                console.print(f"  名称: {roadmap_status.get('title', roadmap_status.get('name', '未知'))}")
                                console.print(f"  描述: {roadmap_status.get('description', '无描述')}")
                                console.print(f"  状态: {roadmap_status.get('status', '未知')}")
                                if not entity_data:
                                    logger.debug(
                                        f"Roadmap (ID: {roadmap_id}) status details might be directly in roadmap_status or missing. Data: {roadmap_status}"
                                    )
                                else:
                                    logger.warning(f"Roadmap (ID: {roadmap_id}) entity_data is not a dict. Data: {entity_data}")
                        else:
                            error_msg = roadmap_status.get("error", "获取失败") if isinstance(roadmap_status, dict) else "获取失败或返回格式不正确"
                            console.print(f"  名称: 无法获取 ({error_msg})")
                            console.print(f"  描述: 无法获取")
                    except Exception as rs_e:
                        console.print(f"  详情: 无法获取 ({rs_e})")
            except Exception as e:
                logger.error(f"显示路线图信息时出错: {e}")
        else:
            # JSON输出
            output_result(result, format, "system" if entity_type is None else entity_type, verbose)

        return 0
    except Exception as e:
        logger.error(f"获取系统状态时出错: {e}", exc_info=True)
        console.print(f"错误: {e}")
        return 1
