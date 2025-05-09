"""
GitHub链接操作模块

提供路线图与GitHub项目之间的链接建立和查询功能。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 用于循环检测的模块级变量
_call_counts = {"find_roadmap_by_github_link": 0, "link_roadmap_to_github_project": set()}  # 使用集合存储调用签名


def link_roadmap_to_github_project(
    service, local_roadmap_id: str, github_owner: str, github_repo: str, github_project_identifier: str
) -> Dict[str, Any]:
    """
    将本地路线图与指定的GitHub项目关联，并将配置存入ProjectState

    Args:
        service: 路线图服务实例
        local_roadmap_id: 本地路线图ID
        github_owner: GitHub仓库所有者
        github_repo: GitHub仓库名称
        github_project_identifier: GitHub项目编号 (UI Number) 或 Node ID

    Returns:
        Dict[str, Any]: 关联结果
    """
    result = {"success": False, "message": "", "data": None}

    # 循环检测 - 使用模块级变量
    # 创建调用签名 - 用于检测重复调用
    call_signature = f"{local_roadmap_id}:{github_owner}:{github_repo}:{github_project_identifier}"

    # 检查是否已经处理过相同的请求
    if call_signature in _call_counts["link_roadmap_to_github_project"]:
        logger.warning(f"检测到重复调用: {call_signature}，可能存在循环依赖，跳过处理")
        result["message"] = "检测到重复调用，操作已跳过，避免潜在循环"
        result["success"] = True  # 返回成功避免更多错误
        return result

    # 将当前调用添加到调用栈
    _call_counts["link_roadmap_to_github_project"].add(call_signature)
    logger.info(f"处理路线图关联请求: {call_signature}")

    try:
        # 验证参数
        if not all([local_roadmap_id, github_owner, github_repo, github_project_identifier]):
            result["message"] = "参数不足，请提供local_roadmap_id, github_owner, github_repo, 和 github_project_identifier"
            return result

        # 确保GitHubSyncService的api_facade已初始化
        if not service.github_sync or not service.github_sync.api_facade:
            result["message"] = "GitHub API Facade未初始化，无法验证GitHub项目。请确保GitHub Token已配置。"
            logger.error(result["message"])
            return result

        api_facade = service.github_sync.api_facade

        try:
            # 尝试通过编号或Node ID获取GitHub项目
            gh_project = None
            project_number = None
            logger.info(f"正在尝试获取GitHub项目: {github_owner}/{github_repo} #{github_project_identifier}")

            if github_project_identifier.startswith("PVT_") or github_project_identifier.startswith("PVTPROJ_"):
                # 这是Node ID，需要从所有项目中筛选
                logger.info(f"尝试通过Node ID {github_project_identifier}查找GitHub项目")
                gh_project = api_facade.projects_client.get_project_by_node_id(github_project_identifier)
                if gh_project:
                    logger.info(f"通过Node ID找到GitHub项目: {gh_project.get('title')} (#{gh_project.get('number')})")
                else:
                    logger.warning(f"通过Node ID {github_project_identifier} 未找到项目。")
            else:
                # 尝试将标识符转换为数字
                try:
                    project_number = int(github_project_identifier)
                    logger.info(f"尝试通过项目编号 {project_number} 查找GitHub项目")

                    # 首先尝试使用repository查询
                    try:
                        gh_project = api_facade.projects_client.get_project_v2(github_owner, github_repo, project_number)
                        if gh_project:
                            logger.info(f"通过repository.projectV2找到GitHub项目: {gh_project.get('title')} (#{gh_project.get('number')})")
                    except Exception as e:
                        logger.warning(f"通过repository.projectV2获取项目失败: {e}")

                    # 如果失败，尝试使用viewer查询
                    if not gh_project:
                        logger.info(f"尝试通过viewer.projectV2获取项目 #{project_number}")
                        gh_project = api_facade.projects_client.get_project_v2_by_viewer(project_number)
                        if gh_project:
                            logger.info(f"通过viewer.projectV2找到GitHub项目: {gh_project.get('title')} (#{gh_project.get('number')})")
                except (ValueError, TypeError) as e:
                    logger.error(f"GitHub项目标识符 '{github_project_identifier}' 无法转换为整数: {e}")
                    result["message"] = f"无效的GitHub项目标识符: {github_project_identifier}。应为数字项目编号或以'PVT_'开头的Node ID。"
                    return result

            if not gh_project:
                error_message = f"无法在GitHub上找到项目: {github_owner}/{github_repo} (标识符: {github_project_identifier})."
                # 添加更具体的错误提示
                if project_number is not None:
                    error_message += f" 请确认项目编号 {project_number} 是否正确，或尝试使用Node ID。"
                error_message += " 请检查以下可能原因: 1) GitHub项目编号或ID错误; 2) GitHub Token无权访问该项目; 3) 该项目可能不是ProjectV2类型。"
                result["message"] = error_message
                logger.error(error_message)
                return result

            # 获取项目详情
            project_node_id = gh_project.get("id")  # Node ID
            project_ui_number = gh_project.get("number")  # UI Number
            project_title = gh_project.get("title")  # 修正from "name" to "title"

            if not all([project_node_id, project_ui_number is not None, project_title]):
                result["message"] = f"获取GitHub项目详细信息不完整。检查Node ID, UI Number, 和 Title: {gh_project}"
                logger.error(result["message"])
                return result

            # 获取ProjectState实例
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            project_state = status_service.project_state

            # 检查是否已建立相同的关联
            existing_project_id = project_state.get_github_project_id_for_roadmap(local_roadmap_id)
            if existing_project_id == project_node_id:
                logger.info(f"路线图 {local_roadmap_id} 已关联到相同的GitHub项目 {project_node_id}，跳过更新")
                result["success"] = True
                result["message"] = f"路线图 {local_roadmap_id} 已关联到GitHub项目 {project_title}"
                return result

            # 1. 更新github_project_map
            project_state.set_roadmap_github_project(local_roadmap_id, project_node_id)
            logger.info(f"已在ProjectState的github_project_map中关联路线图 {local_roadmap_id} 到GitHub项目Node ID {project_node_id}")

            # 2. 如果当前活动路线图是这个local_roadmap_id，则更新active_roadmap_backend_config
            current_active_roadmap_id = project_state.get_current_roadmap_id()
            if current_active_roadmap_id == local_roadmap_id:
                github_backend_config = {"project_id": project_node_id, "project_number": project_ui_number, "project_title": project_title}
                current_total_backend_config = project_state.get_active_roadmap_backend_config()
                if not isinstance(current_total_backend_config, dict):
                    current_total_backend_config = {}
                current_total_backend_config["github"] = github_backend_config  # 只更新github部分
                project_state.set_active_roadmap_backend_config(current_total_backend_config)

                logger.info(f"已更新当前活动路线图 ({local_roadmap_id}) 的GitHub后端配置 (不含owner/repo): {current_total_backend_config}")

            result["success"] = True
            result["message"] = f"成功将本地路线图 '{local_roadmap_id}' 关联到GitHub项目 '{project_title}' ({github_owner}/{github_repo}#P{project_ui_number})"
            result["data"] = {
                "local_roadmap_id": local_roadmap_id,
                "github_owner": github_owner,
                "github_repo": github_repo,
                "github_project_node_id": project_node_id,
                "github_project_number": project_ui_number,
                "github_project_title": project_title,
            }
            return result

        except Exception as e:
            result["message"] = f"关联路线图到GitHub项目时出错: {e}"
            logger.error(result["message"], exc_info=True)
            return result
    finally:
        # 无论成功与否，从调用栈中移除当前调用
        if call_signature in _call_counts["link_roadmap_to_github_project"]:
            _call_counts["link_roadmap_to_github_project"].remove(call_signature)
            logger.info(f"调用栈移除: {call_signature}")


def find_roadmap_by_github_link(owner: str, repo: str, project_identifier: str) -> Optional[str]:
    """
    根据GitHub项目信息查找关联的本地路线图

    Args:
        owner: GitHub用户名或组织名
        repo: GitHub仓库名
        project_identifier: GitHub项目标识符（Number或Node ID）

    Returns:
        Optional[str]: 关联的本地路线图ID，如果未找到则返回None
    """
    try:
        # 循环检测 - 使用模块级变量
        _call_counts["find_roadmap_by_github_link"] += 1

        if _call_counts["find_roadmap_by_github_link"] > 5:  # 限制最大调用深度
            logger.warning(f"find_roadmap_by_github_link递归调用次数过多({_call_counts['find_roadmap_by_github_link']})，可能存在循环依赖")
            _call_counts["find_roadmap_by_github_link"] = 0  # 重置计数器
            return None

        logger.info(f"查找路线图关联: owner={owner}, repo={repo}, project_identifier={project_identifier}")

        # 1. 尝试从StatusService中获取映射信息
        from src.status.service import StatusService

        status_service = StatusService.get_instance()
        project_state = status_service.project_state

        # roadmap_configs = project_state.get_all_roadmap_backend_configs() # 方法不存在
        all_mappings = project_state.get_all_roadmap_github_mappings()  # roadmap_id -> github_project_node_id

        global_owner = status_service.get_settings_value("github_info.default_owner")
        global_repo = status_service.get_settings_value("github_info.default_repo")

        # logger.debug(f"查找关联: owner={owner}, repo={repo}, identifier={project_identifier}")
        # logger.debug(f"所有后端配置: {roadmap_configs}")
        logger.debug(f"所有 রোডম্যাপ-GitHub Project ID 映射: {all_mappings}")
        logger.debug(f"全局 GitHub 配置: owner={global_owner}, repo={global_repo}")

        # if not roadmap_configs:
        #     logger.warning("ProjectState 中没有可用的路线图后端配置")
        #     return None

        # for roadmap_id, backends in roadmap_configs.items():
        #     if "github" in backends:
        #         gh_config = backends["github"]
        #         # 检查 owner, repo 和 project_id/project_number 是否匹配
        #         config_owner = gh_config.get("owner")
        #         config_repo = gh_config.get("repo")
        #         config_project_id = gh_config.get("project_id") # Node ID
        #         config_project_number = gh_config.get("project_number")

        #         # 确保 owner 和 repo 匹配
        #         if config_owner == owner and config_repo == repo:
        #             # 检查 project_identifier (可能是 Node ID 或 Number)
        #             if project_identifier == config_project_id or str(project_identifier) == str(config_project_number):
        #                 logger.info(f"找到匹配的本地路线图 {roadmap_id} 对应 GitHub 项目 {project_identifier}")
        #                 return roadmap_id

        # 新的逻辑：直接使用 all_mappings 和全局 owner/repo
        if global_owner == owner and global_repo == repo:
            for roadmap_id, github_node_id in all_mappings.items():
                if project_identifier == github_node_id:  # 假设 project_identifier 总是 Node ID
                    logger.info(f"找到匹配的本地路线图 {roadmap_id} 对应 GitHub 项目 Node ID {project_identifier}")
                    return roadmap_id
                # 如果 project_identifier 可能是 project number，则需要进一步处理
                # 目前 GitHubProjectSync 主要使用 Node ID 进行精确匹配

        logger.warning(f"未找到与 GitHub 项目 (owner: {owner}, repo: {repo}, identifier: {project_identifier}) 关联的本地路线图")
        return None

    except Exception as e:
        logger.error(f"查找与GitHub项目关联的路线图时出错: {e}", exc_info=True)
        _call_counts["find_roadmap_by_github_link"] = 0  # 出错时也重置计数器
        return None
