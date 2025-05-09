"""
GitHub 信息状态提供者模块
"""

import logging
import os
import subprocess
from typing import Any, Dict, Optional, Tuple

from src.core.config import get_config
from src.status.interfaces import IStatusProvider

# 导入配置来源枚举
from src.status.models import StatusSource
from src.utils.git_utils import get_git_remote_info

logger = logging.getLogger(__name__)


class GitHubInfoProvider(IStatusProvider):
    """提供当前项目关联的 GitHub 仓库信息状态"""

    def __init__(self):
        """初始化 GitHub 信息提供者"""
        self._domain = "github_info"

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return self._domain

    @staticmethod
    def is_gh_authenticated() -> bool:
        """检查 GitHub CLI 是否已认证"""
        try:
            # 使用 gh auth status 检查认证状态
            # --hostname github.com 确保检查的是 GitHub 主站的认证
            process = subprocess.run(["gh", "auth", "status", "--hostname", "github.com"], capture_output=True, text=True, check=False)
            # 认证成功时，信息通常在 stdout 中，stderr 可能为空或包含其他非错误信息
            # 当 RC=0 并且 stdout 包含登录成功信息时，认为已认证
            if process.returncode == 0 and "Logged in to github.com" in process.stdout:
                logger.info("GitHub CLI 已认证.")
                return True
            else:
                logger.warning(
                    f"GitHub CLI 未认证或认证状态检查失败. RC: {process.returncode}, STDOUT: {process.stdout.strip()}, STDERR: {process.stderr.strip()}"
                )
                return False
        except FileNotFoundError:
            logger.error("GitHub CLI (gh) 未找到。请确保已安装并配置在 PATH 中。")
            return False
        except Exception as e:
            logger.error(f"检查 GitHub CLI 认证状态时发生未知错误: {e}", exc_info=True)
            return False

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取 GitHub 仓库配置信息状态 (owner, repo) 和 CLI 认证状态。

        优先级:
        1. settings.json (权威配置来源)
        2. 环境变量 GITHUB_OWNER/GITHUB_REPO (可被 settings.json 覆盖或写入 settings.json)
        3. 本地 Git 检测 (仅用于初始化时的默认建议值)

        不再从此 provider 获取 GitHub Project (V2) 的 ID 或 Title。
        这些 Project 特定的信息由 ProjectState 管理。
        """
        logger.info("GitHubInfoProvider: get_status called")
        status_data = {
            "env_owner": None,
            "env_repo": None,
            "settings_owner": None,
            "settings_repo": None,
            "detected_owner": None,
            "detected_repo": None,
            "effective_owner": None,
            "effective_repo": None,
            "is_cli_authenticated": False,
            "source": StatusSource.FALLBACK.value,
            "configured": False,  # 指 owner 和 repo 是否已配置
            "status_message": None,
            "error_message": None,  # 重命名 "error" 为 "error_message" 以更清晰
        }

        # 1. 从环境变量获取 GITHUB_OWNER 和 GITHUB_REPO
        status_data["env_owner"] = os.environ.get("GITHUB_OWNER")
        status_data["env_repo"] = os.environ.get("GITHUB_REPO")
        logger.info(f"从环境变量检测: GITHUB_OWNER={status_data['env_owner']}, GITHUB_REPO={status_data['env_repo']}")

        # 2. 从 settings.json 获取配置 (这是权威来源)
        try:
            from src.status.service import StatusService

            status_service = StatusService.get_instance()
            # 使用 StatusService 的方法获取已加载的配置
            settings_github = status_service.get_settings_value("github_info", default={})
            # 确保获取到的是字典
            if not isinstance(settings_github, dict):
                settings_github = {}
                logger.warning("settings.json 中的 github_info 不是字典格式，将视为空配置。")

            status_data["settings_owner"] = settings_github.get("owner")
            status_data["settings_repo"] = settings_github.get("repo")
            logger.info(f"从 StatusService 获取的GitHub配置: owner={status_data['settings_owner']}, repo={status_data['settings_repo']}")

        except ImportError:
            logger.error("无法导入 StatusService，无法获取 settings.json 配置。")
            status_data["error_message"] = "无法加载状态服务以读取配置。"
        except Exception as e:
            logger.error(f"通过 StatusService 获取 GitHub 配置时出错: {e}", exc_info=True)
            status_data["error_message"] = f"获取 GitHub 配置失败: {e}"

        # 3. 确定 effective_owner 和 effective_repo
        if status_data["settings_owner"] and status_data["settings_repo"]:
            status_data["effective_owner"] = status_data["settings_owner"]
            status_data["effective_repo"] = status_data["settings_repo"]
            status_data["source"] = StatusSource.SETTINGS_JSON.value
            status_data["configured"] = True
            logger.info(f"使用 settings.json 中的 GitHub 配置: {status_data['effective_owner']}/{status_data['effective_repo']}")
        elif status_data["env_owner"] and status_data["env_repo"]:
            status_data["effective_owner"] = status_data["env_owner"]
            status_data["effective_repo"] = status_data["env_repo"]
            status_data["source"] = StatusSource.ENV_VARIABLE.value
            status_data["configured"] = True  # 环境变量也视为有效配置，init时会写入settings
            logger.info(f"使用环境变量中的 GitHub 配置: {status_data['effective_owner']}/{status_data['effective_repo']}")
        else:
            status_data["configured"] = False
            status_data["source"] = StatusSource.FALLBACK.value

        # 4. 尝试检测本地 Git 仓库信息 (仅用于初始化时的默认建议，不影响 configured 状态)
        try:
            detected_owner, detected_repo = get_git_remote_info()
            status_data["detected_owner"] = detected_owner
            status_data["detected_repo"] = detected_repo
            logger.info(f"本地检测的Git仓库信息: owner={detected_owner}, repo={detected_repo}")
        except Exception as e:
            logger.warning(f"检测Git仓库信息失败: {e}")

        # --- Revised status_message logic ---
        base_message = ""
        if status_data["configured"]:
            # Configured case might not need a base message unless there's a warning later
            base_message = ""
        elif detected_owner and detected_repo:
            base_message = f"GitHub仓库通过Git检测为 {detected_owner}/{detected_repo}，但未在VibeCopilot中正式配置。请运行 'vc status init' 进行确认和配置。"
        else:
            base_message = "GitHub仓库未配置。请运行 'vc status init' 或设置 GITHUB_OWNER/GITHUB_REPO 环境变量。"

        # Check auth status
        status_data["is_cli_authenticated"] = self.is_gh_authenticated()
        auth_warning = ""
        if not status_data["is_cli_authenticated"]:
            # Add a leading space for clean concatenation if base_message exists
            auth_warning = " GitHub CLI 未认证。请运行 'gh auth login' 并确保 GITHUB_TOKEN 环境变量已设置。"

        # Combine messages
        if base_message and auth_warning:
            status_data["status_message"] = base_message + auth_warning
        elif auth_warning:
            # Use strip() in case base_message was empty or only spaces
            status_data["status_message"] = auth_warning.strip()
        elif base_message:
            status_data["status_message"] = base_message
        else:
            # If configured and authenticated, message is None
            status_data["status_message"] = None

        logger.info(
            f"GitHubInfoProvider.get_status 完成。Effective: {status_data['effective_owner']}/{status_data['effective_repo']}, Configured: {status_data['configured']}, CLI Auth: {status_data['is_cli_authenticated']}, Source: {status_data['source']}"
        )
        return status_data

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """GitHub 信息提供者不支持更新操作"""
        return {"updated": False, "error": "GitHubInfoProvider 不支持更新操作"}

    def list_entities(self, status: Optional[str] = None) -> list:
        """GitHub 信息提供者不支持列出实体"""
        return []
