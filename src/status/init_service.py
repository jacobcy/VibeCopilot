"""
初始化服务模块

负责项目初始化、目录结构创建和基础配置设置
"""

import datetime
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.config import get_config
from src.core.config.settings import SettingsConfig
from src.status.service import StatusService
from src.sync.github_project import GitHubProjectSync
from src.sync.utils import check_gh_auth, check_gh_installed

logger = logging.getLogger(__name__)


class InitService:
    """初始化服务类

    负责项目初始化、目录结构创建和基础配置设置
    """

    def __init__(self):
        """初始化服务实例"""
        self.base_dir = "."
        self.config = get_config()
        self.project_root = Path(os.getcwd())
        self.is_vibecopilot_project = self.project_root.name == "VibeCopilot"

    def initialize_project(self, project_name: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """执行完整项目初始化流程

        Args:
            project_name: 项目名称，如未提供则使用目录名
            force: 是否强制初始化

        Returns:
            Dict: 初始化结果
        """
        result = {
            "status": "success",
            "project_name": project_name or self.project_root.name,
            "is_vibecopilot_project": self.is_vibecopilot_project,
            "checks": {},
        }

        # 1. 检查项目结构并创建必要的目录和初始配置文件
        structure_result = self.check_project_structure(force)
        result["checks"]["structure"] = structure_result
        if not structure_result["success"]:
            result["status"] = "error"
            result["error"] = "项目结构检查失败"
            return result

        # 检查 settings.json 是否成功创建
        settings_path = os.path.join(self.base_dir, ".vibecopilot/config/settings.json")
        if not os.path.exists(settings_path):
            result["status"] = "error"
            result["error"] = "settings.json 不存在，无法继续初始化。"
            logger.error(result["error"])
            return result

        # 2. 检查集成状态
        integrations_result = self.check_integrations()
        result["checks"]["integrations"] = integrations_result

        # 3. 检查basic-memory工具
        memory_result = self.check_memory_tool()
        result["checks"]["memory_tool"] = memory_result

        # 4. 创建示例文件(如果是VibeCopilot项目)
        if self.is_vibecopilot_project:
            example_files_result = self.create_example_files()
            result["checks"]["example_files"] = example_files_result

        # 5. 确保 ProjectState 也被正确初始化或更新
        if result["status"] == "success":
            actual_project_name = result["project_name"]
            try:
                # 获取状态服务实例
                status_service = StatusService.get_instance()

                # 首先检查是否已经有有效的活动roadmap
                current_roadmap = self._check_current_roadmap(status_service)

                # 获取 GitHub 项目信息（如果存在）
                github_project_info = None
                if "integrations" in result["checks"] and "github" in result["checks"]["integrations"]:
                    github_info = result["checks"]["integrations"]["github"]
                    if github_info.get("project_exists"):
                        github_project_info = {
                            "project_id": github_info.get("project_id"),
                            "project_title": github_info.get("project_title"),
                            "project_number": github_info.get("project_number"),
                        }

                # 只有在当前没有有效roadmap时，或强制初始化时，才进行roadmap关联
                if not current_roadmap["valid"] or force:
                    if github_project_info:
                        logger.info(f"将使用GitHub项目 '{github_project_info['project_title']}' (#{github_project_info['project_number']}) 关联roadmap")

                    # 调用 StatusService 的方法来确保 ProjectState 被正确初始化/更新
                    init_status_result = status_service.initialize_project_status(
                        project_name=actual_project_name, github_project_info=github_project_info
                    )

                    if init_status_result.get("status") == "success":
                        logger.info(f"ProjectState for '{actual_project_name}' initialized/updated successfully via StatusService.")
                        result["checks"]["project_state_init"] = init_status_result
                    else:
                        error_message = init_status_result.get("error", "Unknown error during ProjectState init")
                        logger.error(f"Failed to initialize/update ProjectState for '{actual_project_name}' via StatusService: {error_message}")
                        result["checks"]["project_state_init"] = {"success": False, "error": error_message}
                else:
                    logger.info(f"检测到有效的活动roadmap (ID: {current_roadmap['roadmap_id']}), 跳过roadmap初始化")
                    result["checks"]["project_state_init"] = {
                        "success": True,
                        "message": f"已有有效roadmap (ID: {current_roadmap['roadmap_id']}), 无需重新初始化",
                        "roadmap_id": current_roadmap["roadmap_id"],
                    }
            except Exception as e:
                logger.error(f"Error during final ProjectState initialization via StatusService: {e}", exc_info=True)
                error_str = str(e)
                result["checks"]["project_state_init"] = {"success": False, "error": error_str}

        return result

    def check_project_structure(self, force: bool = False) -> Dict[str, Any]:
        """检查并创建项目目录结构

        Args:
            force: 是否强制创建

        Returns:
            Dict: 检查结果
        """
        result = {"success": True, "messages": [], "created_dirs": [], "failed_dirs": []}

        # 定义核心目录结构
        core_dirs = {".ai": "Agent工作目录", ".vibecopilot": "VibeCopilot项目管理目录"}

        # 定义子目录结构
        subdirs = {
            ".ai/memory": "Agent记忆存储",
            ".ai/roadmap": "路线图数据",
            ".ai/workflows": "工作流定义",
            ".ai/templates": "提示模板",
            ".vibecopilot/config": "项目配置",
            ".vibecopilot/status": "项目状态",
            ".vibecopilot/tasks": "任务管理",
            ".vibecopilot/logs": "日志文件",
        }

        # 检查并创建目录
        for dir_path, description in {**core_dirs, **subdirs}.items():
            full_path = os.path.join(self.base_dir, dir_path)
            if not os.path.exists(full_path):
                try:
                    os.makedirs(full_path)
                    result["created_dirs"].append(dir_path)
                    result["messages"].append(f"创建目录: {dir_path} ({description})")
                    logger.info(f"创建目录: {dir_path}")
                except Exception as e:
                    result["failed_dirs"].append(dir_path)
                    result["messages"].append(f"创建目录失败: {dir_path} - {str(e)}")
                    result["success"] = False
                    logger.error(f"创建目录失败: {dir_path} - {e}")

        # 初始化配置文件
        config_result = self._init_config_files(force)
        result["messages"].extend(config_result["messages"])
        if not config_result["success"]:
            result["success"] = False

        return result

    def _init_config_files(self, force: bool = False) -> Dict[str, Any]:
        """初始化配置文件

        Args:
            force: 是否强制创建

        Returns:
            Dict: 初始化结果
        """
        result = {"success": True, "messages": []}

        # 获取项目名称（默认使用当前目录名）
        project_name = os.path.basename(os.path.abspath(self.base_dir))

        # 基础配置
        settings = {
            "project": {"name": project_name, "version": "0.1.0", "description": "VibeCopilot项目"},
            "paths": {
                "ai_dir": ".ai",
                "config_dir": ".vibecopilot/config",
                "status_dir": ".vibecopilot/status",
                "tasks_dir": ".vibecopilot/tasks",
                "logs_dir": ".vibecopilot/logs",
            },
        }

        # 创建或更新settings.json
        settings_path = os.path.join(self.base_dir, ".vibecopilot/config/settings.json")

        if os.path.exists(settings_path) and not force:
            # 文件已存在，读取它并仅更新可能的环境变量配置
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing_settings = json.load(f)

                # 尝试从环境变量获取GitHub配置
                github_owner = os.getenv("GITHUB_OWNER")
                github_repo = os.getenv("GITHUB_REPO")
                roadmap_project_name = os.getenv("ROADMAP_PROJECT_NAME", "VibeRoadmap")

                # 只有当环境变量中有相关配置时，才更新settings.json
                updated = False

                # 确保存在github_info节点
                if "github_info" not in existing_settings:
                    existing_settings["github_info"] = {}

                if github_owner and github_owner != existing_settings.get("github_info", {}).get("owner"):
                    existing_settings["github_info"]["owner"] = github_owner
                    logger.info(f"从环境变量更新GitHub配置: owner = {github_owner}")
                    updated = True

                if github_repo and github_repo != existing_settings.get("github_info", {}).get("repo"):
                    existing_settings["github_info"]["repo"] = github_repo
                    logger.info(f"从环境变量更新GitHub配置: repo = {github_repo}")
                    updated = True

                if roadmap_project_name and roadmap_project_name != existing_settings.get("github_info", {}).get("project_name"):
                    existing_settings["github_info"]["project_name"] = roadmap_project_name
                    logger.info(f"从环境变量更新GitHub配置: project_name = {roadmap_project_name}")
                    updated = True

                if updated:
                    with open(settings_path, "w", encoding="utf-8") as f:
                        json.dump(existing_settings, f, indent=2, ensure_ascii=False)
                    result["messages"].append("更新配置文件: settings.json (从环境变量)")
                    logger.info("从环境变量更新配置文件: settings.json")
                else:
                    result["messages"].append("配置文件已存在，无需更新: settings.json")
                    logger.info("配置文件已存在，无需更新: settings.json")

            except Exception as e:
                result["messages"].append(f"读取或更新配置文件失败: settings.json - {str(e)}")
                result["success"] = False
                logger.error(f"读取或更新配置文件失败: settings.json - {e}", exc_info=True)
        else:
            # 文件不存在或强制重新创建
            try:
                # 尝试从环境变量获取GitHub配置
                github_owner = os.getenv("GITHUB_OWNER")
                github_repo = os.getenv("GITHUB_REPO")
                roadmap_project_name = os.getenv("ROADMAP_PROJECT_NAME", "VibeRoadmap")

                # 如果有环境变量配置，添加到settings
                if github_owner and github_repo:
                    settings["github_info"] = {"owner": github_owner, "repo": github_repo, "project_name": roadmap_project_name}
                    logger.info(f"从环境变量添加GitHub配置: {github_owner}/{github_repo}")

                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)

                if force:
                    result["messages"].append("强制重新创建配置文件: settings.json")
                    logger.info("强制重新创建配置文件: settings.json")
                else:
                    result["messages"].append("创建配置文件: settings.json")
                    logger.info("创建配置文件: settings.json")
            except Exception as e:
                result["messages"].append(f"创建配置文件失败: settings.json - {str(e)}")
                result["success"] = False
                logger.error(f"创建配置文件失败: settings.json - {e}", exc_info=True)

        return result

    def check_integrations(self) -> Dict[str, Any]:
        """检查项目集成配置

        Returns:
            Dict: 检查结果
        """
        result = {"github": self._check_github_integration(), "llm": self._check_llm_integration()}
        return result

    def _check_github_integration(self) -> Dict[str, Any]:
        """检查 GitHub 集成状态，包括 CLI 和项目。"""
        result = {
            "configured": False,
            "cli_installed": False,
            "authenticated": False,
            "project_exists": False,
            "project_id": None,
            "project_title": None,
            "status_message": "",
            "error": None,
        }
        github_sync = GitHubProjectSync()  # 实例化 GitHubProjectSync, 后续可能需要

        try:
            # 检查 GitHub CLI 是否安装
            gh_check = check_gh_installed()
            result["cli_installed"] = gh_check["installed"]
            if not result["cli_installed"]:
                result["status_message"] = "GitHub CLI 未安装。"
                logger.warning(result["status_message"])
                return result
            logger.info(f"GitHub CLI 已安装: {gh_check.get('version', '未知版本')}")

            # 检查 GitHub CLI 认证状态
            gh_auth_status = check_gh_auth()
            result["authenticated"] = gh_auth_status["authenticated"]
            if not result["authenticated"]:
                result["status_message"] = "GitHub CLI 未认证。请运行 'gh auth login'。"
                logger.warning(result["status_message"])
                return result

            # 读取settings.json中的GitHub配置 (使用正确的方法)
            settings_config = SettingsConfig()
            github_owner = settings_config.get("github_info.owner")
            github_repo = settings_config.get("github_info.repo")

            if github_owner and github_repo:
                result["configured"] = True
                logger.info(f"GitHub 配置已在settings.json中设置: {github_owner}/{github_repo}")
            else:
                result["status_message"] = "GitHub 未在settings.json中配置owner和repo。"
                logger.warning(result["status_message"])
                return result

            # 使用 gh project list 获取远程项目缓存数据 (使用正确的格式)
            logger.info("获取GitHub项目列表...")
            try:
                # 首先检查是否已存在 VibeRoadmap 项目，避免重复创建
                # 使用 --json 参数获取 JSON 格式输出
                gh_project_list = subprocess.run(["gh", "project", "list", "--format", "json"], capture_output=True, text=True)

                if gh_project_list.returncode == 0:
                    try:
                        # 解析JSON输出
                        projects_data = json.loads(gh_project_list.stdout)
                        projects_count = projects_data.get("totalCount", 0)
                        logger.info(f"成功获取GitHub项目列表, 共{projects_count}个项目")

                        # 查找所有名为"VibeRoadmap"的项目，选择第一个
                        vibe_roadmap_projects = []
                        for project in projects_data.get("projects", []):
                            if project.get("title") == "VibeRoadmap":
                                vibe_roadmap_projects.append(project)
                                logger.info(f"找到VibeRoadmap项目: #{project.get('number')} (ID: {project.get('id')})")

                        if vibe_roadmap_projects:
                            # 使用第一个找到的项目
                            vibe_roadmap_project = vibe_roadmap_projects[0]
                            result["project_exists"] = True
                            result["project_id"] = vibe_roadmap_project.get("id")
                            result["project_title"] = vibe_roadmap_project.get("title")
                            result["project_number"] = vibe_roadmap_project.get("number")
                            result["status_message"] = f"使用已有GitHub Project: {result['project_title']} (#{result['project_number']})"
                            logger.info(result["status_message"])

                            # 如果找到多个，记录警告
                            if len(vibe_roadmap_projects) > 1:
                                logger.warning(f"发现多个同名VibeRoadmap项目，使用第一个 (#{vibe_roadmap_project.get('number')})")
                            return result
                    except json.JSONDecodeError as e:
                        logger.error(f"解析GitHub项目列表时出错: {e}")
                        # 但不要直接返回，继续尝试其他方法
                else:
                    logger.warning(f"获取项目列表失败: {gh_project_list.stderr}")
                    # 但不要直接返回，继续尝试其他方法

                # 如果上面的方法失败，或者没有找到项目，使用传统的命令行格式
                logger.info("使用传统命令行格式查找VibeRoadmap项目...")
                gh_project_list_raw = subprocess.run(["gh", "project", "list"], capture_output=True, text=True)

                if gh_project_list_raw.returncode == 0:
                    # 解析纯文本输出
                    lines = gh_project_list_raw.stdout.strip().split("\n")
                    found_project = False

                    # 跳过表头
                    if len(lines) > 1:
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 3 and "VibeRoadmap" in line:
                                try:
                                    project_number = parts[0]
                                    project_id = parts[-1]  # 最后一列通常是ID
                                    result["project_exists"] = True
                                    result["project_id"] = project_id
                                    result["project_title"] = "VibeRoadmap"
                                    result["project_number"] = project_number
                                    result["status_message"] = f"使用已有GitHub Project: VibeRoadmap (#{project_number})"
                                    logger.info(result["status_message"])
                                    found_project = True
                                    break
                                except Exception as e:
                                    logger.error(f"解析项目行时出错: {e}")

                    # 只有在确实没有找到项目时才创建新项目
                    if not found_project and not result["project_exists"]:
                        logger.info("未找到VibeRoadmap项目，尝试创建...")
                        create_project_result = subprocess.run(
                            ["gh", "project", "create", "VibeRoadmap", "--format", "json"], capture_output=True, text=True
                        )

                        if create_project_result.returncode == 0:
                            try:
                                new_project = json.loads(create_project_result.stdout)
                                result["project_exists"] = True
                                result["project_id"] = new_project.get("id")
                                result["project_title"] = new_project.get("title") or "VibeRoadmap"
                                result["project_number"] = new_project.get("number")
                                logger.info(f"成功创建GitHub Project: {result['project_title']} (#{result['project_number']})")
                            except json.JSONDecodeError as e:
                                logger.error(f"解析新项目信息时出错: {e}")
                                # 创建成功但无法解析详情，返回基本信息
                                result["project_exists"] = True
                                result["project_title"] = "VibeRoadmap"
                                logger.info("项目可能已创建，但无法解析详细信息")
                        else:
                            result["status_message"] = "无法创建新项目。"
                            logger.error(f"创建项目失败: {create_project_result.stderr}")
                else:
                    result["status_message"] = "无法获取或创建GitHub项目。"
                    logger.error(f"项目列表和创建操作均失败")
            except Exception as e:
                logger.error(f"处理GitHub项目时出错: {e}", exc_info=True)
                result["error"] = f"处理GitHub项目时出错: {e}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"GitHub 集成检查失败: {e}", exc_info=True)

        return result

    def _check_llm_integration(self) -> Dict[str, Any]:
        """检查LLM集成配置

        Returns:
            Dict: 检查结果
        """
        llm_result = {"enabled": False, "configured": False, "providers": [], "messages": []}

        # 检查是否启用LLM
        project_config_path = self.project_root / ".vibecopilot/config/settings.json"
        if project_config_path.exists():
            try:
                project_config = file_utils.read_json_file(str(project_config_path))
                llm_result["enabled"] = project_config.get("features", {}).get("enable_llm", False)
            except Exception:
                pass

        # 检查常见LLM API密钥
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY") or self.config.get("ai.openai.api_key"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY") or self.config.get("ai.anthropic.api_key"),
            "cohere": os.getenv("COHERE_API_KEY"),
        }

        available_providers = [name for name, key in api_keys.items() if key]
        llm_result["providers"] = available_providers

        # 如果未从项目配置中确定，则根据是否有可用提供商来确定
        if not llm_result["enabled"] and available_providers:
            llm_result["enabled"] = True

        llm_result["configured"] = bool(available_providers)

        # 对于VibeCopilot项目，即使没有API密钥也视为已配置
        if self.is_vibecopilot_project and not available_providers:
            llm_result["messages"].append("未找到LLM API密钥，但在VibeCopilot项目中这是可接受的")
            llm_result["configured"] = True

        return llm_result

    def check_memory_tool(self) -> Dict[str, Any]:
        """检查basic-memory工具配置

        Returns:
            Dict: 检查结果
        """
        memory_result = {"tool_installed": False, "project_initialized": False, "messages": []}

        # 检查basic-memory工具是否安装
        try:
            # 尝试运行basic-memory命令检查其可用性
            result = subprocess.run(["basic-memory", "--version"], capture_output=True, text=True, check=False)
            memory_result["tool_installed"] = result.returncode == 0

            if memory_result["tool_installed"]:
                memory_result["messages"].append(f"basic-memory工具已安装: {result.stdout.strip()}")

                # 检查当前项目是否已初始化
                project_check = subprocess.run(["basic-memory", "project", "info"], capture_output=True, text=True, check=False)

                # 如果退出码为0，表示项目已初始化
                if project_check.returncode == 0:
                    memory_result["project_initialized"] = True
                    memory_result["messages"].append("basic-memory项目已初始化")
                else:
                    memory_result["messages"].append("basic-memory项目未初始化")
            else:
                memory_result["messages"].append("basic-memory工具未安装或无法运行")
        except Exception as e:
            logger.error(f"检查basic-memory工具时出错: {e}")
            memory_result["messages"].append(f"检查basic-memory工具时出错: {e}")

        return memory_result

    def create_example_files(self) -> Dict[str, Any]:
        """为VibeCopilot项目创建示例文件

        Returns:
            Dict: 操作结果
        """
        result = {"success": True, "messages": [], "created_files": []}

        # 检查.env.example是否存在
        example_env_path = self.project_root / ".env.example"
        example_env_source = self.project_root / "config/example.env"

        if not example_env_path.exists() and example_env_source.exists():
            try:
                # 从config/example.env复制内容而不是硬编码
                shutil.copy2(example_env_source, example_env_path)
                result["created_files"].append(".env.example")
                result["messages"].append("已复制config/example.env到.env.example文件")
            except Exception as e:
                logger.error(f"创建.env.example文件失败: {e}")
                result["messages"].append(f"创建.env.example文件失败: {e}")
                result["success"] = False
        elif not example_env_source.exists():
            logger.warning("config/example.env模板文件不存在，无法创建.env.example")
            result["messages"].append("config/example.env模板文件不存在，无法创建.env.example")

        # 可以添加其他示例文件的创建逻辑

        return result

    def _check_current_roadmap(self, status_service) -> Dict[str, Any]:
        """检查当前活动roadmap是否有效

        Args:
            status_service: StatusService实例

        Returns:
            Dict: 包含roadmap验证结果
        """
        result = {"valid": False, "roadmap_id": None, "message": ""}

        try:
            # 获取当前roadmap状态
            project_state = status_service.get_project_state()
            active_roadmap_id = project_state.get("active_roadmap_id") if project_state else None

            if not active_roadmap_id:
                result["message"] = "当前没有活动的roadmap"
                return result

            # 检查指定的roadmap是否存在于数据库中
            # 使用状态服务检查roadmap是否有效
            roadmap_check = status_service.check_roadmap_exists(active_roadmap_id)

            if roadmap_check.get("exists", False):
                result["valid"] = True
                result["roadmap_id"] = active_roadmap_id
                result["message"] = f"找到有效的活动roadmap (ID: {active_roadmap_id})"
                logger.info(result["message"])
            else:
                result["message"] = f"指定的活动roadmap (ID: {active_roadmap_id}) 无效或不存在"
                logger.warning(result["message"])
        except Exception as e:
            result["message"] = f"检查当前roadmap时出错: {str(e)}"
            logger.error(result["message"], exc_info=True)

        return result
