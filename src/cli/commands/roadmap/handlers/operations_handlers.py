"""
路线图操作处理器模块

提供路线图操作的处理逻辑，直接调用底层服务。
"""

import logging
from typing import Any, Dict, Optional

from rich.console import Console

from src.roadmap.service import RoadmapService
from src.sync.utils import get_github_sync_config_for_push  # Assuming this util or similar can get owner/repo
from src.utils import console_utils

logger = logging.getLogger(__name__)
console = Console()


def export_to_yaml(service, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    导出路线图到YAML文件

    直接调用export_service.export_to_yaml，避免多层调用链

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图
        output_path: 输出文件路径，不提供则使用默认路径

    Returns:
        Dict[str, Any]: 导出结果
    """
    # 直接从export_service导入RoadmapExportService
    from src.sync.export_service import RoadmapExportService

    # 创建导出服务实例并直接调用
    export_service = RoadmapExportService(service)
    return export_service.export_to_yaml(roadmap_id, output_path)


def handle_link_github(
    project_identifier: Optional[str] = None,
    local_roadmap_id: Optional[str] = None,
    list_links: bool = False,
    ctx_obj: Optional[Any] = None,  # Renamed from roadmap_service to avoid confusion
    **kwargs,  # Catch any unexpected args
) -> Dict[str, Any]:
    """
    处理路线图与GitHub项目关联操作或列出链接。

    Args:
        project_identifier: GitHub项目编号或Node ID (用于创建链接)
        local_roadmap_id: 要关联的本地路线图ID (默认为当前活动路线图，用于创建链接)
        list_links: 如果为True，则列出现有链接。
        ctx_obj: Click传递的对象，用于获取服务实例。
        **kwargs: 其他可能的参数 (将被忽略)

    Returns:
        Dict[str, Any]: 包含操作结果的字典
    """
    # 从 ctx_obj 获取 RoadmapService 实例 (假设 ctx_obj 是 CLIContext 或类似对象)
    roadmap_service: Optional[RoadmapService] = None
    if hasattr(ctx_obj, "roadmap_service") and isinstance(ctx_obj.roadmap_service, RoadmapService):
        roadmap_service = ctx_obj.roadmap_service
    else:
        try:
            # 作为后备，尝试直接获取
            from src.roadmap.service.service_connector import get_roadmap_service

            roadmap_service = get_roadmap_service()
        except Exception as e:
            logger.error(f"获取 RoadmapService 失败: {e}")
            return {"success": False, "message": f"内部错误: 无法获取路线图服务 ({e})"}

    if not roadmap_service:
        return {"success": False, "message": "内部错误: 路线图服务不可用。"}

    # 处理 --list 操作
    if list_links:
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            project_state = status_service.project_state
            all_mappings = project_state.get_all_roadmap_github_mappings()
            return {"success": True, "message": "成功获取链接列表", "links": all_mappings}
        except Exception as e:
            logger.error(f"获取链接列表时出错: {e}", exc_info=True)
            return {"success": False, "message": f"获取链接列表时出错: {e}"}

    # --- 处理创建链接操作 --- #
    if not project_identifier:
        return {"success": False, "message": "错误: 创建链接时必须提供 --project-identifier。"}

    try:
        # 1. 从全局配置获取 owner 和 repo
        owner: Optional[str] = None
        repo: Optional[str] = None
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            github_config = status_service.get_domain_status("github_info")
            if github_config and github_config.get("configured", False):
                owner = github_config.get("effective_owner")
                repo = github_config.get("effective_repo")

            if not owner or not repo:
                raise ValueError("未在配置中找到有效的 GitHub owner 或 repo。")

        except ValueError as e:
            logger.error(f"获取 owner/repo 配置失败: {e}")
            return {"success": False, "message": f"获取 GitHub 配置失败: {e} 请运行 'vc status init' 检查或完成配置。"}
        except Exception as e:  # Catch other potential errors during config fetch
            logger.error(f"获取 owner/repo 配置时发生意外错误: {e}", exc_info=True)
            return {"success": False, "message": f"获取 GitHub 配置时发生意外错误。请检查日志。"}

        # 2. 获取要关联的本地路线图ID
        local_roadmap_id_to_link = local_roadmap_id or roadmap_service.active_roadmap_id
        if not local_roadmap_id_to_link:
            return {"success": False, "message": "没有活动的路线图，请先切换或通过 --roadmap-id 指定一个路线图。"}

        # 3. 验证本地路线图是否存在
        local_roadmap = roadmap_service.get_roadmap(local_roadmap_id_to_link)
        if not local_roadmap:
            return {"success": False, "message": f"找不到指定的本地路线图 ({local_roadmap_id_to_link})"}

        # 4. 调用RoadmapService中的方法执行关联操作
        result = roadmap_service.link_roadmap_to_github_project(
            local_roadmap_id=local_roadmap_id_to_link,
            github_owner=owner,  # Use fetched owner
            github_repo=repo,  # Use fetched repo
            github_project_identifier=project_identifier,
        )

        return result

    except Exception as e:
        logger.error(f"link操作执行失败: {e}", exc_info=True)
        return {"success": False, "message": f"关联GitHub项目时出错: {str(e)}"}


def handle_validate(source: str, verbose: bool = False) -> Dict[str, Any]:
    """
    验证路线图YAML文件格式

    Args:
        source: 源文件路径
        verbose: 是否显示详细信息

    Returns:
        Dict[str, Any]: 包含验证结果的字典
    """
    from src.validation.roadmap_validation import RoadmapValidator

    try:
        # 创建验证器
        validator = RoadmapValidator()

        # 验证文件
        is_valid, warnings, errors = validator.validate_file(source)

        # 返回验证结果
        result = {
            "success": is_valid,
            "warnings": warnings,
            "errors": errors,
            "message": "验证通过，文件格式完全符合要求" if is_valid and not warnings and not errors else None,
        }

        if not is_valid:
            result["message"] = "验证失败，文件格式有错误"
        elif warnings:
            result["message"] = "验证通过，但有警告需要注意"

        return result

    except Exception as e:
        error_details = None
        if verbose:
            import traceback

            error_details = traceback.format_exc()

        logger.error(f"验证文件时出错: {e}", exc_info=True)
        return {"success": False, "message": f"验证文件时出错: {str(e)}", "error_details": error_details}
