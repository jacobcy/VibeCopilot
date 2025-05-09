"""
路线图GitHub同步处理器模块

提供路线图与GitHub项目的同步处理逻辑。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console

from src.core.config import get_config
from src.roadmap.service.roadmap_service import RoadmapService
from src.roadmap.service.roadmap_service_facade import RoadmapServiceFacade
from src.roadmap.service.service_connector import get_roadmap_service
from src.status.service import StatusService
from src.sync.github_project import GitHubProjectSync
from src.sync.utils import check_gh_auth
from src.utils import console_utils
from src.utils.git_utils import get_git_remote_info

logger = logging.getLogger(__name__)
console = Console()


async def handle_sync_roadmap(
    service, operation: str, id: Optional[str], force: bool, verbose: bool  # 将 service 放在第一个位置  # 将 force 放在前面
) -> Dict[str, Any]:
    """
    处理路线图与GitHub项目的同步操作 (简化版，调用Facade服务)。
    """
    roadmap_service_instance = None
    try:
        roadmap_service_instance = get_roadmap_service()  # 优先通过连接器获取
        if not roadmap_service_instance:
            logger.error("无法通过连接器获取 RoadmapService 实例。")
            # 可以尝试从 service 参数获取，但这通常不应该是主要方式
            if hasattr(service, "roadmap_service") and isinstance(service.roadmap_service, RoadmapService):
                roadmap_service_instance = service.roadmap_service
                logger.info("通过 service 参数获取了 RoadmapService 实例。")
            else:
                raise ValueError("无法获取 RoadmapService 实例。请确保服务已正确初始化。")

        if not isinstance(roadmap_service_instance, RoadmapService):
            raise TypeError(f"获取到的服务实例类型不正确: {type(roadmap_service_instance)}，期望是 RoadmapService")

    except Exception as e:
        logger.error(f"获取 RoadmapService 实例失败: {e}", exc_info=True)
        console_utils.print_error(f"内部错误: 获取路线图服务失败 ({e})")
        return {"status": "error", "message": f"获取路线图服务失败: {str(e)}"}

    console.print(f"[bold cyan]=== 执行路线图同步 ({operation}) ===[/bold cyan]")

    # 1. 检查 GitHub CLI 认证状态 (保留在 handler 层作为前置检查)
    try:
        auth_status = check_gh_auth()
        if not auth_status.get("authenticated"):
            console_utils.print_error("GitHub CLI 未认证。请运行 'gh auth login' 进行认证。")
            return {"status": "error", "message": "GitHub CLI 未认证。"}
        else:
            console_utils.print_info("GitHub CLI 已认证。")
    except Exception as e:
        logger.error(f"GitHub 认证检查失败: {e}", exc_info=True)
        console_utils.print_error(f"GitHub 认证检查失败: {str(e)}")
        return {"status": "error", "message": f"GitHub 认证检查失败: {str(e)}"}

    # 2. 调用 Facade 服务层方法
    sync_result = None
    try:
        if operation == "push":
            local_id_arg = id
            if local_id_arg is None:
                # Facade 层会处理 active_roadmap_id，这里可以传递 None
                # 但为了更明确，可以先尝试获取 active_id
                active_id = roadmap_service_instance.active_roadmap_id
                if active_id:
                    local_id_arg = active_id
                    console_utils.print_info(f"未指定本地路线图ID，使用当前活动路线图 (ID: {local_id_arg})...")
                else:
                    console_utils.print_error("执行 push 操作时，必须提供本地路线图ID，或设置一个活动路线图。")
                    return {"status": "error", "message": "缺少本地路线图ID。"}

            console_utils.print_info(f"正在调用服务层推送同步: local_roadmap_id={local_id_arg}, force={force}")
            # 注意：Facade 方法不是异步的
            sync_result = roadmap_service_instance.push_to_github(local_roadmap_id=local_id_arg, force=force)

        elif operation == "pull":
            remote_identifier_arg = id
            if not remote_identifier_arg:
                console_utils.print_error("执行 pull 操作时，必须提供远程 GitHub Project 的编号或Node ID。")
                return {"status": "error", "message": "缺少远程项目标识符。"}

            console_utils.print_info(f"正在调用服务层拉取同步: remote_project_identifier={remote_identifier_arg}, force={force}")
            # 注意：Facade 方法不是异步的
            sync_result = roadmap_service_instance.pull_from_github(remote_project_identifier=remote_identifier_arg, force=force)

        else:
            # CLI 框架通常会阻止无效的操作类型，这里是最后的保障
            console_utils.print_error(f"内部错误: 无效的操作类型 '{operation}'")
            return {"status": "error", "message": f"无效的操作类型 {operation}"}

    except Exception as e:
        logger.error(f"调用同步服务时发生意外错误: {e}", exc_info=True)
        console_utils.print_error(f"同步过程中发生意外错误: {str(e)}")
        return {"status": "error", "message": f"同步时发生意外错误: {str(e)}"}

    # 3. 显示结果
    if sync_result:
        if sync_result.get("status") == "success":
            console_utils.print_success(sync_result.get("message", "同步操作成功完成。"))
            # 可以选择性地显示 data 或 stats (如果存在且 verbose)
            if verbose and sync_result.get("data") and sync_result["data"].get("stats"):
                console_utils.print_info("同步统计:")
                stats = sync_result["data"]["stats"]
                for key, value in stats.items():
                    console.print(f"  - {key.replace('_', ' ').capitalize()}: {value}")
        else:
            console_utils.print_error(sync_result.get("message", "同步操作失败。"))
    else:
        # 如果 sync_result 为 None (理论上不应发生，除非前面逻辑有误)
        console_utils.print_error("同步操作未返回有效结果。")
        return {"status": "error", "message": "同步操作未返回有效结果。"}

    # 返回最终结果字典给调用者 (CLI 框架)
    return sync_result
