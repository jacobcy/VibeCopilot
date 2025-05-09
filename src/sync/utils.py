"""
Sync Utilities Module

Provides helper functions for synchronization processes, especially with GitHub.
"""
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def get_github_sync_config_for_push(target_roadmap_id: str) -> Dict[str, Any]:
    """获取 GitHub "Push" 同步所需的核心配置。

    Args:
        target_roadmap_id: 目标本地路线图ID。

    Returns:
        Dict[str, Any]: 包含配置信息的字典，如果关键配置缺失则 'success' 为 False。
                       Keys: 'success', 'owner', 'repo', 'project_node_id',
                             'project_title', 'project_number', 'message' (in case of error)
    """
    config_data: Dict[str, Any] = {
        "success": False,
        "owner": None,
        "repo": None,
        "project_node_id": None,
        "project_title": "[未指定项目标题]",
        "project_number": None,
        "message": "",
    }

    try:
        from src.status.service import StatusService
        from src.sync.github_project import GitHubProjectSync  # For fetching project details

        status_service = StatusService.get_instance()
        project_state = status_service.project_state

        # 1. 获取全局 owner/repo
        global_github_info = status_service.get_settings_value("github_info", {})
        owner = global_github_info.get("owner")
        repo = global_github_info.get("repo")

        if not owner or not repo:
            config_data["message"] = "全局GitHub配置 (owner/repo) 不完整。请检查 settings.json。"
            logger.error(config_data["message"])
            return config_data

        config_data["owner"] = owner
        config_data["repo"] = repo

        # 2. 获取目标路线图的 GitHub Project Node ID 映射
        project_node_id = project_state.get_github_project_id_for_roadmap(target_roadmap_id)

        if not project_node_id:
            config_data["message"] = f"路线图 {target_roadmap_id} 未与任何 GitHub Project 关联。请先链接。"
            logger.error(config_data["message"])
            return config_data  # 返回错误，因为没有 project_node_id 无法继续 push

        config_data["project_node_id"] = project_node_id

        # 3. 获取关联的 GitHub Project 的 number 和 title (如果可能)
        # 这个信息对于 get_or_create_project (在 GitHubSyncService 中调用) 很重要
        # 并且也用于日志和错误消息
        try:
            github_sync_helper = GitHubProjectSync()
            all_projects_result = github_sync_helper.get_github_projects()  # 这会获取当前 owner/repo 下的所有项目
            if all_projects_result.get("success"):
                found_project = None
                for proj in all_projects_result.get("projects", []):
                    if proj.get("id") == project_node_id:  # 确保比较的是 Node ID
                        found_project = proj
                        break
                if found_project:
                    config_data["project_number"] = found_project.get("number")
                    config_data["project_title"] = found_project.get("title", config_data["project_title"])
                    logger.info(
                        f"工具函数: 为 Node ID {project_node_id} 获取到项目详情: Title='{config_data['project_title']}', Number={config_data['project_number']}"
                    )
                else:
                    logger.warning(f"工具函数: 在远程项目列表中未找到 Node ID {project_node_id} 对应的项目。项目标题可能不准确。")
            else:
                logger.warning(f"工具函数: 无法获取远程 GitHub 项目列表来查找项目详情: {all_projects_result.get('message')}")
        except Exception as e_fetch_details:
            logger.warning(f"工具函数: 获取远程 GitHub 项目列表以查找项目详情时出错: {e_fetch_details}")
            # 即使这里出错，也继续，只是 project_title/number 可能不准确

        config_data["success"] = True
        return config_data

    except ImportError as ie:
        msg = f"导入模块失败 (可能存在循环依赖或路径问题): {ie}"
        logger.critical(msg, exc_info=True)
        config_data["message"] = msg
        return config_data
    except Exception as e:
        msg = f"获取 GitHub push 同步配置时发生意外错误: {e}"
        logger.error(msg, exc_info=True)
        config_data["message"] = msg
        return config_data


def get_github_sync_config_for_pull(remote_project_identifier: str) -> Dict[str, Any]:
    """获取 GitHub "Pull" 同步所需的核心配置。

    Args:
        remote_project_identifier: 远程 GitHub Project 的 Node ID 或编号。

    Returns:
        Dict[str, Any]: 包含配置信息的字典，如果关键配置缺失则 'success' 为 False。
                       Keys: 'success', 'owner', 'repo',
                             'remote_project_node_id', 'remote_project_title',
                             'remote_project_number',
                             'message' (in case of error)
    """
    config_data: Dict[str, Any] = {
        "success": False,
        "owner": None,
        "repo": None,
        "remote_project_node_id": None,
        "remote_project_title": "[未知远程项目标题]",
        "remote_project_number": None,
        "message": "",
    }

    try:
        from src.status.service import StatusService
        from src.sync.github_project import GitHubProjectSync

        status_service = StatusService.get_instance()
        # project_state = status_service.project_state # Not needed here anymore

        # 1. 获取全局 owner/repo
        global_github_info = status_service.get_settings_value("github_info", {})
        owner = global_github_info.get("owner")
        repo = global_github_info.get("repo")

        if not owner or not repo:
            config_data["message"] = "全局GitHub配置 (owner/repo) 不完整。请检查 settings.json。"
            logger.error(config_data["message"])
            return config_data

        config_data["owner"] = owner
        config_data["repo"] = repo

        # 2. 获取远程 GitHub Project 的详细信息 (Node ID, Title, Number)
        #    这需要使用 GitHubProjectSync().get_project_details_by_identifier
        #    该方法内部会处理 owner 和 repo (从 settings 或参数传入)
        #    为了安全起见，确保 GitHubProjectSync 使用正确的 owner/repo
        try:
            github_sync_helper = GitHubProjectSync()  # 它会从 settings 获取默认 owner/repo
            remote_details_result = github_sync_helper.get_project_details_by_identifier(identifier=remote_project_identifier)
            if not remote_details_result.get("success") or not remote_details_result.get("project"):
                config_data[
                    "message"
                ] = f"无法获取远程 GitHub Project (Identifier: {remote_project_identifier}) 的详细信息: {remote_details_result.get('message', '未知错误')}"
                logger.error(config_data["message"])
                return config_data

            remote_project = remote_details_result["project"]
            config_data["remote_project_node_id"] = remote_project["id"]
            config_data["remote_project_title"] = remote_project.get("title", config_data["remote_project_title"])
            config_data["remote_project_number"] = remote_project.get("number")
            logger.info(
                f"工具函数: 获取到远程项目信息: Title='{config_data['remote_project_title']}', NodeID={config_data['remote_project_node_id']}, Number={config_data['remote_project_number']}"
            )

        except Exception as e_fetch_remote:
            config_data["message"] = f"查找远程 GitHub 项目 (Identifier: {remote_project_identifier}) 时出错: {e_fetch_remote}"
            logger.error(config_data["message"], exc_info=True)
            return config_data

        config_data["success"] = True
        return config_data

    except ImportError as ie:
        msg = f"导入模块失败 (可能存在循环依赖或路径问题): {ie}"
        logger.critical(msg, exc_info=True)
        config_data["message"] = msg
        return config_data
    except Exception as e:
        msg = f"获取 GitHub pull 同步配置时发生意外错误: {e}"
        logger.error(msg, exc_info=True)
        config_data["message"] = msg
        return config_data


# 可以在这里添加 get_github_sync_config_for_pull 函数

# GitHub CLI Checkers - To be moved from GitHubProjectSync


def check_gh_installed() -> Dict[str, Any]:
    """检查是否安装了GitHub CLI

    Returns:
        Dict: 检查结果 (keys: "installed", "version", "message")
    """
    result = {"installed": False, "version": None, "message": ""}
    try:
        import subprocess  # Ensure subprocess is imported

        process = subprocess.run(["gh", "--version"], capture_output=True, text=True, check=False)
        if process.returncode == 0:
            result["installed"] = True
            version_text = process.stdout.strip()
            result["version"] = version_text.split("\n")[0] if "\n" in version_text else version_text
            result["message"] = "GitHub CLI已安装"
        else:
            result["message"] = "GitHub CLI未安装或无法正常运行"
    except FileNotFoundError:  # More specific exception for gh not found
        result["message"] = "GitHub CLI 'gh' 命令未找到。请确保已安装并添加到系统PATH。"
        logger.warning(result["message"])
    except Exception as e:
        result["message"] = f"检查GitHub CLI时出错: {str(e)}"
        logger.error(result["message"], exc_info=True)
    return result


def check_gh_auth() -> Dict[str, Any]:
    """检查GitHub CLI认证状态

    Returns:
        Dict: 认证状态结果 (keys: "authenticated", "user", "message")
    """
    result = {"authenticated": False, "user": None, "message": ""}
    gh_installed_check = check_gh_installed()  # Call the util version
    if not gh_installed_check["installed"]:
        result["message"] = f"无法检查认证状态: {gh_installed_check['message']}"
        return result
    try:
        import subprocess  # Ensure subprocess is imported

        process = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=False)
        if process.returncode == 0:
            result["authenticated"] = True
            output = process.stdout
            if "Logged in to" in output and "as" in output:
                user_part = output.split("as")[1].strip().split()[0].strip()
                result["user"] = user_part
            result["message"] = "GitHub CLI已认证"
        else:
            # More specific error message for auth failure
            error_output = process.stderr.strip() if process.stderr else process.stdout.strip()
            result["message"] = f"GitHub CLI未认证。请运行 'gh auth login'。详情: {error_output}"
            logger.warning(result["message"])

    except FileNotFoundError:  # Should be caught by check_gh_installed, but as a safeguard
        result["message"] = "GitHub CLI 'gh' 命令未找到。"
        logger.warning(result["message"])
    except Exception as e:
        result["message"] = f"检查GitHub认证状态时出错: {str(e)}"
        logger.error(result["message"], exc_info=True)
    return result
