"""
GitHub项目同步模块

负责VibeCopilot与GitHub Project之间的同步和管理功能
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from src.sync.utils import check_gh_auth, check_gh_installed  # Import from utils

logger = logging.getLogger(__name__)


class GitHubProjectSync:
    """GitHub项目同步类

    负责与GitHub Project进行同步和管理
    """

    def __init__(self):
        """初始化GitHub项目同步实例"""
        logger.debug("GitHubProjectSync 实例已创建")

    def _get_github_config(self) -> Dict[str, Any]:
        """通过StatusService获取GitHub配置，并在缺失时抛出错误"""
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            github_info = status_service.get_domain_status("github_info")
            logger.info(f"从StatusService获取的GitHub信息: {github_info}")
            if github_info:
                if github_info.get("configured", False):
                    owner = github_info.get("effective_owner")
                    repo = github_info.get("effective_repo")
                    token = os.getenv("GITHUB_TOKEN") or github_info.get("effective_token")
                    logger.info(f"已获取有效配置: owner={owner}, repo={repo}")
                    return {"owner": owner, "repo": repo, "token": token}
                else:
                    error_msg = github_info.get("status_message") or "GitHub配置未完成，请执行 'vc status init' 命令"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                logger.error("未能从StatusService获取GitHub信息")
                raise ValueError("未能获取GitHub信息，请执行 'vc status init' 命令配置GitHub信息")
        except Exception as e:
            if isinstance(e, ValueError) and "请执行 'vc status init'" in str(e):
                raise
            logger.error(f"获取GitHub配置时出错: {e}")
            raise ValueError(f"获取GitHub配置失败，请执行 'vc status init' 命令配置GitHub信息: {e}")

    def _run_gh_command(self, command_parts: List[str], token: Optional[str] = None) -> Tuple[int, str, str]:
        """执行给定的 gh 命令并返回结果。

        Args:
            command_parts: 命令及其参数的列表 (例如 ['gh', 'project', 'list', '--owner', owner_name])
            token: 可选的 GitHub token，用于设置 GITHUB_TOKEN 环境变量。

        Returns:
            Tuple[int, str, str]: 返回码, stdout, stderr
        """
        logger.debug(f"准备执行 GH 命令: {' '.join(command_parts)}")
        env = os.environ.copy()
        if token:
            env["GITHUB_TOKEN"] = token

        try:
            process = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                check=False,  # আমরা এখানে চেক=ফলস ব্যবহার করব যাতে আমরা রিটার্ন কোড ম্যানুয়ালি পরিচালনা করতে পারি
                env=env,
            )
            stdout = process.stdout.strip() if process.stdout else ""
            stderr = process.stderr.strip() if process.stderr else ""
            logger.debug(f"GH 命令执行完毕。返回码: {process.returncode}, stdout: '{stdout[:100]}...', stderr: '{stderr[:100]}...'")
            return process.returncode, stdout, stderr
        except FileNotFoundError:
            logger.error(f"GH 命令 '{command_parts[0]}' 未找到。请确保 GitHub CLI 已安装并添加到系统PATH。")
            return -1, "", f"命令 '{command_parts[0]}' 未找到。"
        except Exception as e:
            logger.error(f"执行 GH 命令时发生意外错误: {e}", exc_info=True)
            return -1, "", f"执行 GH 命令时发生意外错误: {e}"

    def get_github_projects(self) -> Dict[str, Any]:
        """获取GitHub项目列表"""
        logger.info("====== 获取GitHub项目列表 ======")
        result = {"success": False, "projects": [], "message": ""}

        auth_status = check_gh_auth()
        if not auth_status.get("authenticated", False):
            result["message"] = auth_status.get("message", "GitHub CLI 未认证")
            return result

        try:
            github_config = self._get_github_config()
            owner = github_config["owner"]
            token = github_config.get("token")
        except ValueError as e:
            result["message"] = str(e)
            return result

        cmd = ["gh", "project", "list", "--owner", owner]
        returncode, stdout, stderr = self._run_gh_command(cmd, token)

        if returncode == 0:
            try:
                lines = stdout.strip().split("\n")
                if len(lines) > 1:
                    lines = lines[1:]  # Skip header
                projects = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            number = int(parts[0])
                            state = parts[-2]
                            node_id = parts[-1]  # Changed from 'id' to 'node_id' for clarity
                            title_parts = parts[1:-2]
                            title = " ".join(title_parts)
                            projects.append({"number": number, "title": title, "state": state, "id": node_id})
                        except Exception as parse_e:
                            logger.warning(f"解析项目行 '{line}' 时出错: {parse_e}")
                result["projects"] = projects
                result["success"] = True
                result["message"] = f"成功获取GitHub项目列表，共{len(projects)}个项目"
            except Exception as parse_e:
                result["message"] = f"解析GitHub项目列表输出时出错: {parse_e}"
                logger.error(f"解析GH项目列表时出错: {parse_e}", exc_info=True)
        else:
            result["message"] = f"获取GitHub项目列表失败 (错误码: {returncode}): {stderr}"
            logger.error(f"GH project list命令失败: {stderr}")
            if "This command needs the 'read:project' and 'read:org' scopes" in stderr:
                result["message"] = "GitHub token没有足够的权限。请运行 'gh auth login' 并确保包含 'read:project' 和 'read:org' 权限。"

        return result

    def find_project_by_title(self, title: str) -> Dict[str, Any]:
        """通过标题查找GitHub项目

        Args:
            title: 项目标题

        Returns:
            Dict: 项目信息或错误
        """
        logger.info(f"====== 通过标题 '{title}' 查找GitHub项目 ======")
        result = {"success": False, "project": None, "message": ""}

        # 首先获取所有项目
        projects_result = self.get_github_projects()
        if not projects_result["success"]:
            result["message"] = projects_result["message"]
            return result

        # 在项目列表中查找匹配标题的项目
        found_project = None
        for project in projects_result["projects"]:
            if project["title"] == title:
                found_project = project
                break

        if found_project:
            result["success"] = True
            result["project"] = found_project
            result["message"] = f"成功找到项目 '{title}'"
        else:
            result["message"] = f"未找到标题为 '{title}' 的项目"

        return result

    def create_github_project(self, title: str, description: str = "") -> Dict[str, Any]:
        """创建新的GitHub项目

        Args:
            title: 项目标题
            description: 项目描述 (可选)

        Returns:
            Dict: 创建结果
        """
        logger.info(f"====== 创建新的GitHub项目: '{title}' ======")
        result = {"success": False, "project": None, "message": ""}

        auth_status = check_gh_auth()
        if not auth_status.get("authenticated", False):
            result["message"] = auth_status.get("message", "GitHub CLI 未认证")
            return result

        try:
            github_config = self._get_github_config()
            owner = github_config["owner"]
            token = github_config.get("token")
        except ValueError as e:
            result["message"] = str(e)
            return result

        cmd = ["gh", "project", "create", title, "--owner", owner]
        if description:
            cmd.extend(["--description", description])
        # 为了获取新创建项目的ID，我们需要JSON输出
        cmd.extend(["--format", "json"])

        returncode, stdout, stderr = self._run_gh_command(cmd, token)

        if returncode == 0:
            try:
                project_data = json.loads(stdout)
                result["success"] = True
                result["project"] = project_data
                # project_data 应该包含 id (node_id), number, title, url 等
                result["message"] = f"成功创建GitHub项目 '{project_data.get('title')}' (ID: {project_data.get('id')})"
                logger.info(result["message"])
            except json.JSONDecodeError as e:
                result["message"] = f"创建项目成功，但解析JSON输出失败: {e}. 输出: {stdout}"
                logger.error(result["message"], exc_info=True)
                # 即使JSON解析失败，如果命令成功，也可能认为项目已创建，但不返回project数据
                result["success"] = True  # Command succeeded
        else:
            result["message"] = f"创建GitHub项目 '{title}' 失败 (错误码: {returncode}): {stderr}"
            logger.error(f"GH project create 命令失败: {stderr}")
            if "A project with the same name already exists" in stderr:
                result["message"] = f"创建失败：名为 '{title}' 的项目已存在。"
            elif "GraphQL error: Could not resolve to an Owner with the name" in stderr:
                result["message"] = f"创建失败：找不到名为 '{owner}' 的所有者。请检查owner名称是否正确。"

        return result

    def ensure_github_project(
        self, title: str, description: str = "", auto_create: bool = False, max_retries: int = 3, retry_delay: int = 5
    ) -> Dict[str, Any]:
        """确保指定标题的GitHub项目存在，如果不存在则可以选择创建

        Includes retry logic for finding the project after creation.

        Args:
            title: 项目标题
            description: 项目描述(创建时使用) - 注意：GitHub CLI目前不支持description参数
            auto_create: 是否自动创建不存在的项目
            max_retries: 查找新建项目时的最大重试次数
            retry_delay: 查找新建项目时重试之间的延迟(秒)

        Returns:
            Dict: 操作结果
        """
        import time  # 确保导入time

        result = {"success": False, "exists": False, "created": False, "project": None, "message": ""}

        # 检查GitHub CLI是否已安装
        gh_installed = check_gh_installed()
        if not gh_installed["installed"]:
            result["message"] = "GitHub CLI未安装，无法创建或管理GitHub项目"
            return result

        # 检查GitHub CLI认证状态
        auth_status = check_gh_auth()
        if not auth_status["authenticated"]:
            result["message"] = f"GitHub CLI未认证: {auth_status['message']}"
            return result

        # 验证配置
        try:
            github_config = self._get_github_config()
            owner = github_config["owner"]
            token = github_config.get("token")
            logger.info(f"使用GitHub配置: owner={owner} 查找项目: {title}")
        except ValueError as e:
            result["message"] = str(e)
            return result

        # 首先检查项目是否存在
        logger.info(f"正在查找GitHub项目: '{title}'")
        find_result = self.find_project_by_title(title)

        # 如果成功找到现有项目
        if find_result.get("found", False):
            result["success"] = True
            result["exists"] = True
            result["project"] = find_result["project"]
            result["message"] = f"找到现有GitHub项目: {title}"
            logger.info(f"找到现有GitHub项目: {title} (ID: {find_result['project'].get('number', 'unknown')})")

            # *** 添加：在找到现有项目时保存其信息 ***
            save_result = self.save_project_to_config(find_result["project"])
            if not save_result["success"]:
                result["message"] += f" (警告: 保存项目信息失败: {save_result['message']})"
                logger.warning(f"保存现有GitHub项目信息失败: {save_result['message']}")
            # *** 结束添加 ***

            return result

        # 如果允许自动创建
        if auto_create:
            # 直接尝试创建项目
            logger.info(f"尝试创建GitHub项目: {title}")

            # 直接使用命令行命令创建项目
            cmd = ["gh", "project", "create", "--owner", owner, "--title", title]
            # 注意：GitHub CLI目前不支持description参数

            logger.info(f"执行命令: {' '.join(cmd)}")

            env = os.environ.copy()
            if token:
                env["GITHUB_TOKEN"] = token

            try:
                # 尝试创建项目
                create_process = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)

                # 检查创建结果
                if create_process.returncode == 0:
                    logger.info(f"GitHub项目创建成功: {create_process.stdout}")
                    result["created"] = True
                    result["success"] = True  # 创建成功即视为操作成功
                    result["message"] = f"已成功创建GitHub项目: {title}"

                    # 等待一段时间，然后查找新创建的项目
                    time.sleep(retry_delay)

                    # 尝试查找新创建的项目
                    found_new_project = False
                    for attempt in range(max_retries):
                        logger.info(f"尝试查找新创建的项目 '{title}' (尝试 {attempt + 1}/{max_retries})...")

                        # 每次重试前清空项目列表缓存
                        find_after_create = self.find_project_by_title(title)
                        if find_after_create.get("found", False):
                            result["exists"] = True  # 创建后并找到即标记为存在
                            result["project"] = find_after_create["project"]
                            result["message"] = f"已自动创建并找到GitHub项目: {title}"
                            found_new_project = True

                            # *** 添加：在找到新创建的项目时保存其信息 ***
                            save_result = self.save_project_to_config(find_after_create["project"])
                            if not save_result["success"]:
                                result["message"] += f" (警告: 保存项目信息失败: {save_result['message']})"
                                logger.warning(f"保存新创建的GitHub项目信息失败: {save_result['message']}")
                            # *** 结束添加 ***

                            return result

                        # 如果未找到，等待后重试
                        time.sleep(retry_delay)

                    # 如果重试后仍然找不到
                    result["message"] = f"已成功创建GitHub项目: {title}，但在 {max_retries} 次尝试后（每次间隔 {retry_delay} 秒）仍无法获取详细信息。请稍后手动检查或运行 'vc status init'。"
                    # 注意：此时 result["success"] 仍然是 True，但 result["project"] 是 None
                    return result

                else:
                    # 创建失败
                    stderr = create_process.stderr.strip()
                    logger.error(f"创建GitHub项目失败: {stderr}")

                    # 检查是否是因为项目已存在
                    if "already exists" in stderr.lower() or "已存在" in stderr.lower():
                        logger.info(f"项目 '{title}' 可能已存在，尝试再次查找...")
                        # 等待一下再尝试查找
                        time.sleep(retry_delay)
                        find_existing = self.find_project_by_title(title)
                        if find_existing.get("found", False):
                            # 找到了已存在的项目
                            result["success"] = True
                            result["exists"] = True
                            result["project"] = find_existing["project"]
                            result["message"] = f"项目 '{title}' 已存在，成功找到"

                            # *** 添加：在找到已存在的项目（通过创建失败检查）时保存其信息 ***
                            save_result = self.save_project_to_config(find_existing["project"])
                            if not save_result["success"]:
                                result["message"] += f" (警告: 保存项目信息失败: {save_result['message']})"
                                logger.warning(f"保存已存在的GitHub项目信息失败: {save_result['message']}")
                            # *** 结束添加 ***

                            return result

                    # 如果不是因为项目已存在或者无法找到
                    result["message"] = f"创建GitHub项目失败: {stderr}"
                    return result

            except Exception as e:
                logger.error(f"创建GitHub项目时出错: {e}", exc_info=True)
                result["message"] = f"创建GitHub项目时出错: {e}"
                return result
        else:
            # 不允许自动创建
            result["message"] = f"GitHub项目不存在: {title}，且未启用自动创建"
            # 如果获取项目列表失败，这里的消息可能不够准确，但作为最终fallback可以接受
            if find_result.get("success", False) is False:
                result["message"] = find_result.get("message", result["message"])
                logger.error(f"获取GitHub项目列表失败且未自动创建: {result['message']}")
            return result

    def save_project_to_config(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """将GitHub项目信息保存到配置中

        保存已创建或查找到的GitHub项目信息到两个地方:
        1. StatusService管理的settings.json (设置项目ID)
        2. ProjectState (设置活动项目的项目ID)

        Args:
            project_data: 项目数据，包含项目ID、标题等信息

        Returns:
            Dict: 保存结果
        """
        result = {"success": False, "message": ""}

        if not project_data:
            result["message"] = "未提供项目数据，无法保存"
            return result

        try:
            # 获取项目ID和标题
            # 注意：根据来源不同，字段名可能是number或id
            project_id = None
            if "number" in project_data:
                project_id = project_data["number"]
            elif "id" in project_data:
                project_id = project_data["id"]

            # 获取项目标题
            project_title = project_data.get("title")

            # 记录所有关键字段，便于调试
            logger.info(f"项目数据: {project_data}")
            logger.info(f"提取项目ID={project_id}, 标题={project_title}")

            # 如果项目ID为unknown字符串，设为None以避免后续问题
            if project_id == "unknown":
                project_id = None
                logger.info("项目ID为'unknown'，将设置为None")

            # 新的更新和保存方式
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            github_info_to_update = status_service.get_settings_value("github_info", {})
            if not isinstance(github_info_to_update, dict):
                github_info_to_update = {}
                logger.warning("github_info from settings was not a dict, reinitialized.")

            if project_data.get("owner") and not github_info_to_update.get("owner"):
                github_info_to_update["owner"] = project_data.get("owner")
                logger.info(f"settings.json: 写入缺失的 github_info.owner = {project_data.get('owner')}")
            if project_data.get("repo") and not github_info_to_update.get("repo"):
                github_info_to_update["repo"] = project_data.get("repo")
                logger.info(f"settings.json: 写入缺失的 github_info.repo = {project_data.get('repo')}")

            if github_info_to_update:  # 只有在确实要更新内容（或至少创建空的github_info块）时才调用
                save_result = status_service.update_settings("github_info", github_info_to_update)
            else:
                # 如果 settings 中没有 github_info，且 github_info_to_update 为空，则创建一个空的 github_info。
                if not status_service.get_settings_value("github_info"):  # 检查 settings 中是否已存在 github_info
                    save_result = status_service.update_settings("github_info", {})  # 创建空块
                    logger.info("settings.json: 创建空的 github_info 块因为之前不存在且无内容更新")
                else:
                    save_result = True  # 无内容更新，且已有块，视为成功
                    logger.info("github_info_to_update为空，且settings.json中已存在github_info块，跳过更新。")

            if save_result:
                logger.info(f"成功更新/保存GitHub信息到settings.json")

            # 2. 尝试保存到ProjectState
            try:
                project_state = status_service.project_state

                # 获取当前活动路线图后端配置
                # backend_config = project_state.get_active_roadmap_backend_config("github") # 旧的错误调用
                all_backend_configs = project_state.get_active_roadmap_backend_config()  # 获取整个字典
                if not isinstance(all_backend_configs, dict):
                    all_backend_configs = {}
                    logger.warning("ProjectState中的active_roadmap_backend_config不是字典，已重置为空字典。")

                backend_config = all_backend_configs.get("github", {})  # 获取github部分的配置
                if not isinstance(backend_config, dict):  # 确保是字典
                    backend_config = {}
                    logger.warning("ProjectState中active_roadmap_backend_config的github部分不是字典，已重置为空字典。")

                # 保存项目ID（如果有）
                if project_id:
                    backend_config["project_id"] = project_id
                    logger.info(f"设置ProjectState中的project_id={project_id}")

                # 保存项目标题（如果有）
                if project_title:
                    backend_config["project_title"] = project_title
                    logger.info(f"设置ProjectState中的project_title={project_title}")

                # 确保还有其他基本配置
                github_info = github_info_to_update

                # 更新后端配置
                # project_state.set_active_roadmap_backend_config("github", backend_config) # 旧的调用方式
                all_backend_configs["github"] = backend_config  # 更新github部分
                project_state.set_active_roadmap_backend_config(all_backend_configs)  # 保存整个字典
                logger.info(f"成功保存GitHub配置到ProjectState")

                # 设置结果
                result["success"] = True
                result["message"] = "已成功保存GitHub项目信息"
                if project_id:
                    result["message"] += f" (ID: {project_id})"
                if project_title:
                    result["message"] += f", 标题: {project_title}"
            except Exception as e:
                logger.error(f"保存GitHub配置到ProjectState时出错: {e}", exc_info=True)
                # 即使ProjectState保存失败，只要settings.json保存成功，视为部分成功
                if save_result:
                    result["success"] = True
                    result["message"] = f"已保存GitHub配置到settings.json，但保存到ProjectState失败: {e}"
                else:
                    result["message"] = f"保存GitHub配置失败: {e}"

        except Exception as e:
            logger.error(f"保存GitHub配置时出错: {e}", exc_info=True)
            result["message"] = f"保存GitHub配置时出错: {e}"

        return result

    def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """通过项目ID获取GitHub项目详情

        Args:
            project_id: GitHub项目的Node ID

        Returns:
            Dict: 操作结果，包含项目详情
        """
        result = {"success": False, "project": None, "message": ""}

        # 检查GitHub CLI是否已安装
        gh_installed = check_gh_installed()
        if not gh_installed["installed"]:
            result["message"] = "GitHub CLI未安装，无法获取GitHub项目"
            return result

        # 检查GitHub CLI认证状态
        auth_status = check_gh_auth()
        if not auth_status["authenticated"]:
            result["message"] = f"GitHub CLI未认证: {auth_status['message']}"
            return result

        # 验证配置
        try:
            github_config = self._get_github_config()
            owner = github_config["owner"]
            token = github_config.get("token")
        except ValueError as e:
            result["message"] = str(e)
            return result

        # 使用GitHub CLI获取项目详情 (view命令)
        logger.info(f"尝试获取GitHub项目详情，ID: {project_id}")

        try:
            # gh project view $PROJECT_ID --json number,title,owner,shortDescription,id
            cmd = ["gh", "project", "view", project_id, "--json", "number,title,owner,shortDescription,id"]

            logger.debug(f"执行命令: {' '.join(cmd)}")

            env = os.environ.copy()
            if token:
                env["GITHUB_TOKEN"] = token

            view_process = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)

            if view_process.returncode == 0:
                try:
                    project_data = json.loads(view_process.stdout)
                    result["success"] = True
                    result["project"] = project_data
                    result["message"] = f"成功获取GitHub项目详情: {project_data.get('title', '未知')}"
                    logger.info(f"获取到GitHub项目: {project_data.get('title', '未知')} (#{project_data.get('number', '未知')})")
                    return result
                except json.JSONDecodeError as e:
                    result["message"] = f"解析GitHub项目详情时出错: {e}"
                    return result
            else:
                stderr = view_process.stderr.strip()
                result["message"] = f"获取GitHub项目详情失败: {stderr}"
                return result

        except Exception as e:
            logger.error(f"获取GitHub项目详情时出错: {e}", exc_info=True)
            result["message"] = f"获取GitHub项目详情时出错: {e}"
            return result
