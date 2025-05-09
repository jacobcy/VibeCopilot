"""
状态init子命令

处理初始化项目状态的子命令，检查项目结构和配置设置
"""

import datetime
import logging
import os

import click
from rich.console import Console
from rich.prompt import Confirm

from src.cli.commands.status.output_helpers import output_result
from src.roadmap.service.roadmap_service_facade import RoadmapServiceFacade
from src.status.core.project_state import ProjectState
from src.status.init_service import InitService
from src.status.models import StatusSource
from src.status.providers.github_info_provider import GitHubInfoProvider
from src.status.service import StatusService
from src.sync.github_project import GitHubProjectSync
from src.utils import console_utils, file_utils

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="init")
@click.option("--force", is_flag=True, help="强制初始化，覆盖现有配置")
@click.option("--name", help="项目名称 (此选项将覆盖 .env 中的 PROJECT_NAME 或交互式输入)")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
def init_command(force: bool, name: str = None, verbose: bool = False, format: str = "text"):
    """初始化当前项目的VibeCopilot配置和管理，设置必要的集成。

    如果在VibeCopilot项目本身运行，将进行自举初始化，确保开发环境正确配置。
    对其他项目，将创建必要的目录结构，使其能被VibeCopilot管理。
    """
    # 实例化初始化服务
    init_service = InitService()
    is_vibecopilot_project = init_service.is_vibecopilot_project

    if is_vibecopilot_project:
        console.print("[bold cyan]开始VibeCopilot项目自举初始化...[/bold cyan]")
        console.print("[bold yellow]检测到在VibeCopilot项目中运行，将进行开发环境初始化[/bold yellow]")
    else:
        console.print("[bold cyan]开始项目VibeCopilot环境初始化...[/bold cyan]")

    # 执行初始化流程
    result = init_service.initialize_project(project_name=name, force=force)

    # 处理目录结构检查结果
    structure_result = result["checks"]["structure"]
    if not structure_result["success"]:
        console_utils.print_error("项目结构检查失败，无法继续初始化。")
        # 显示关键消息
        for message in structure_result["messages"]:
            if "失败" in message:
                console.print(f"❌ {message}")
        return 1

    # 显示项目结构检查结果
    console_utils.print_success("项目结构检查完成")
    created_dirs_messages = [msg for msg in structure_result.get("messages", []) if "已创建" in msg and "失败" not in msg]

    if verbose:
        for message in structure_result["messages"]:
            console.print(f"- {message}")
    elif created_dirs_messages:
        console.print("✅ 新创建的目录包括:")
        for msg in created_dirs_messages:
            content_part = msg.split("已创建", 1)[1].strip() if "已创建" in msg else msg
            console.print(f"  - {content_part}")
    elif structure_result.get("created_dirs"):  # 兜底处理
        console.print(f"✅ 已创建 {len(structure_result.get('created_dirs', []))} 个目录。详细信息请使用 --verbose 参数查看。")
    else:
        # 如果没有创建新目录，可以打印一个更明确的消息
        console.print("✅ 所有必需的目录结构已存在，未创建新目录。")

    # 首先，确保 GitHub owner/repo 配置到 settings.json
    # 先与用户交互或使用环境变量配置GitHub设置
    status_service = StatusService.get_instance()  # 获取 StatusService 实例

    # result["checks"]["integrations"]["github"] 包含初始的集成检查状态
    initial_github_check = result.get("checks", {}).get("integrations", {}).get("github", {})
    _configure_github_settings(
        console,
        status_service,
        initial_github_check.get("enabled", False),
        initial_github_check.get("configured", False),  # configured (owner/repo in settings.json)
        initial_github_check.get("authenticated", False),
    )

    # 重新获取 github_info 以反映 _configure_github_settings 可能的更改
    github_info_from_settings = status_service.get_settings_value("github_info", {})
    github_owner = github_info_from_settings.get("owner")
    github_repo = github_info_from_settings.get("repo")
    is_github_settings_configured = bool(github_owner and github_repo)
    is_github_cli_authenticated = GitHubInfoProvider.is_gh_authenticated()  # 直接检查认证状态

    # 处理集成检查结果
    integrations = result["checks"]["integrations"]

    # GitHub集成
    github_check_result = integrations["github"]  # 重命名以避免与模块名冲突，并明确其内容
    # 使用更具体的检查条件替换 "enabled"
    is_github_ready_for_project_ops = (
        github_check_result.get("cli_installed", False)
        and github_check_result.get("authenticated", False)
        and github_check_result.get("configured", False)  # configured 指 owner/repo 在 settings.json
    )

    if is_github_ready_for_project_ops:
        console_utils.print_success("GitHub CLI 已安装、已认证，且仓库已在 settings.json 中配置。")

        # 检查 GitHub Project 是否存在 (这部分逻辑已在 _check_github_integration 中处理)
        if github_check_result.get("project_exists", False):
            project_title = github_check_result.get("project_title", "未知项目")
            project_id = github_check_result.get("project_id", "未知ID")
            console_utils.print_success(f"已找到并连接到 GitHub Project: '{project_title}' (ID: {project_id})")
        elif github_check_result.get("configured"):  # 已配置仓库但项目不存在或未配置标题
            if not github_check_result.get("project_title") and github_check_result.get("status_message"):
                # 如果 project_title 为空，_check_github_integration 中会填充 status_message
                console_utils.print_warning(f"{github_check_result.get('status_message')}")
                console_utils.print_info("请在 settings.json 中配置 'github_info.project_title' 或在后续步骤中创建/关联。")
            else:
                # 有 project_title 但 project_exists 为 false
                console_utils.print_warning(f"GitHub Project '{github_check_result.get('project_title', '具有指定标题的项目')}' 未找到。")
                console_utils.print_info("将在后续步骤中尝试创建或关联 GitHub Project。")
        # else: configured 为 False 的情况， status_message 已由 _check_github_integration 处理并会在下面显示

    elif github_check_result.get("cli_installed", False) and github_check_result.get("authenticated", False):
        # CLI已安装并认证，但 owner/repo 未在 settings.json 中配置
        console_utils.print_warning(f"GitHub CLI 已安装并认证，但仓库信息 (owner/repo) 未在 settings.json 中配置。")
        console_utils.print_info(f"状态信息: {github_check_result.get('status_message', '请配置仓库信息。')}")
        console_utils.print_info("请在后续步骤中配置 GitHub 仓库信息。")
    else:
        # CLI 未安装或未认证
        console_utils.print_warning(f"GitHub CLI 未安装或未认证。")
        console_utils.print_info(f"状态信息: {github_check_result.get('status_message', '请安装和认证 GitHub CLI。')}")

    # 进一步显示来自 _check_github_integration 的具体状态或错误信息（如果之前未完全覆盖）
    if (
        not is_github_ready_for_project_ops
        and github_check_result.get("status_message")
        and "未找到" not in github_check_result.get("status_message", "")
        and "未配置 Project 标题" not in github_check_result.get("status_message", "")
    ):
        # 避免重复打印已处理的 project_exists=False 或 project_title 缺失的消息
        # console_utils.print_info(f"GitHub 集成状态: {github_check_result.get('status_message')}")
        pass  # 具体的状态消息已在上面的条件分支中处理

    if github_check_result.get("error"):
        console_utils.print_error(f"GitHub 集成检查出错: {github_check_result.get('error')}")

    # LLM集成
    llm = integrations["llm"]
    if llm["enabled"]:
        if llm["configured"]:
            if llm["providers"]:
                console_utils.print_success(f"LLM集成配置完成，可用提供商: {', '.join(llm['providers'])}")
            else:
                console_utils.print_info("LLM集成已启用但未配置API密钥")
        else:
            console_utils.print_warning("LLM集成未配置API密钥")
    else:
        console_utils.print_info("LLM集成未启用")

    # 处理basic-memory工具检查结果
    memory_result = result["checks"]["memory_tool"]
    if memory_result["tool_installed"]:
        console_utils.print_success("basic-memory工具已安装")
        if memory_result["project_initialized"]:
            console_utils.print_success("basic-memory项目已初始化")
        else:
            console_utils.print_warning("basic-memory项目未初始化，请稍后手动运行 'vc memory init'")
    else:
        console_utils.print_warning("basic-memory工具未安装，部分记忆功能可能受限。")

    # 处理示例文件创建结果
    if is_vibecopilot_project and "example_files" in result["checks"]:
        example_files_result = result["checks"]["example_files"]
        if example_files_result["success"]:
            created_example_files = example_files_result.get("created_files", [])
            if ".env.example" in created_example_files:
                console_utils.print_success("已创建示例环境变量文件: .env.example")
                console_utils.print_info("👉 请复制 .env.example 为 .env 并根据您的环境修改其内容。")
                # 如果还有其他示例文件，分别打印
                other_examples = [f for f in created_example_files if f != ".env.example"]
                if other_examples:
                    console_utils.print_success(f"已创建其他示例文件: {', '.join(other_examples)}")
            elif created_example_files:  # 如果创建了其他示例文件但没有.env.example
                console_utils.print_success(f"已创建示例文件: {', '.join(created_example_files)}")
        elif example_files_result.get("messages"):
            for msg in example_files_result.get("messages", []):
                if "失败" in msg:
                    console_utils.print_error(msg)
                else:
                    console_utils.print_info(msg)

    # 交互式询问项目基本信息 (项目名, 阶段)等

    # 其次，交互式询问项目基本信息 (项目名, 阶段)
    # _ask_project_info 现在只处理这些，不处理 GitHub Project 关联
    # result 传递给 _ask_project_info 以便它了解初始的集成检查状态
    _ask_project_info(console, result)
    project_state = status_service.project_state  # 获取更新后的 ProjectState
    current_project_name_from_state = project_state.get_project_name()
    if not current_project_name_from_state or current_project_name_from_state == "未设置":
        # 如果 _ask_project_info 后仍然未设置，则使用一个最终的默认值
        current_project_name_from_state = os.path.basename(os.getcwd())
        project_state.set_project_name(current_project_name_from_state)
        logger.info(f"项目名最终设置为: {current_project_name_from_state}")

    # 尝试连接RoadmapService和StatusService
    try:
        # 主动尝试连接服务
        status_service = StatusService.get_instance()
        status_service.connect_roadmap_service()
    except Exception as e:
        logger.error(f"连接RoadmapService时出错: {e}")

    # --- GitHub Project 和本地 Roadmap 核心处理逻辑 ---
    if result["status"] == "success":
        if is_github_settings_configured and is_github_cli_authenticated:
            console.print("[bold yellow]处理 GitHub Project 和本地 Roadmap 关联...[/bold yellow]")

            try:
                # 获取状态服务和路线图服务
                status_service = StatusService.get_instance()
                project_state = status_service.project_state

                # 从src.roadmap模块获取RoadmapService，而不是使用RoadmapServiceFacade
                from src.roadmap.service import RoadmapService

                roadmap_service = RoadmapService()

                # 创建 GitHub 同步工具实例
                github_sync = GitHubProjectSync()

                # 从settings.json获取GitHub配置
                github_owner = status_service.get_settings_value("github_info.owner", "")
                github_repo = status_service.get_settings_value("github_info.repo", "")

                # 步骤1: 检查project_state.json是否有远程GitHub项目映射关系
                current_roadmap_id = project_state.get_current_roadmap_id()
                roadmap_github_mapping = project_state.get_roadmap_github_mapping()
                github_project_id = None

                # 如果有当前roadmap并且映射关系存在
                if current_roadmap_id and roadmap_github_mapping and current_roadmap_id in roadmap_github_mapping:
                    github_project_id = roadmap_github_mapping[current_roadmap_id]
                    logger.info(f"找到当前roadmap ID {current_roadmap_id}的GitHub项目映射: {github_project_id}")

                    # 检查本地roadmap是否存在
                    existing_roadmap = roadmap_service.get_roadmap(current_roadmap_id)
                    if existing_roadmap:
                        logger.info(f"当前roadmap ID {current_roadmap_id} 存在且有效，标题: {existing_roadmap.get('title', '未知')}")
                        console_utils.print_success(f"已找到有效的本地Roadmap(ID: {current_roadmap_id})，与GitHub项目关联有效。")
                        # 保持当前设置，无需进一步操作
                        console.print("[bold yellow]GitHub Project 和本地 Roadmap 处理完成，保持现有关联。[/bold yellow]")

                        # 最终总结
                        if is_vibecopilot_project:
                            console_utils.print_success("🚀 VibeCopilot项目自举初始化完成！")
                        else:
                            console_utils.print_success(f"🚀 项目 {project_state.get_project_name()} 的VibeCopilot环境初始化完成！")
                        console_utils.print_info("运行 'vc status show' 查看项目状态，或 'vc roadmap list' 查看路线图。")
                        return 0  # 直接返回，无需继续处理
                    else:
                        logger.warning(f"映射中的roadmap ID {current_roadmap_id} 在本地不存在，需要重新处理")
                        # 继续执行后续步骤找到或创建新的roadmap

                # 步骤2: 获取GitHub项目信息 - 使用环境变量或settings.json中的配置
                project_title = status_service.get_settings_value("github_info.project_title", "")
                if not project_title:
                    project_title = os.environ.get("ROADMAP_PROJECT_NAME", "VibeRoadmap")  # 默认使用VibeRoadmap

                console_utils.print_info(f"正在查找或创建远程 GitHub Project: '{project_title}'...")

                # 检查是否在init服务中已经找到了项目
                github_integration = result["checks"]["integrations"]["github"]
                remote_project_info = None

                # 如果init服务已经找到了项目，直接使用它
                if github_integration.get("project_exists") and github_integration.get("project_id"):
                    remote_project_node_id = github_integration.get("project_id")
                    remote_project_title = github_integration.get("project_title", project_title)
                    remote_project_number = github_integration.get("project_number", "未知")

                    console_utils.print_success(
                        f"使用已找到的 GitHub Project '{remote_project_title}' (ID: {remote_project_node_id}, Number: {remote_project_number})。"
                    )

                    remote_project_info = {"id": remote_project_node_id, "title": remote_project_title, "number": remote_project_number}
                else:
                    # 如果没有找到项目，确保其存在
                    ensure_result = github_sync.ensure_github_project(
                        title=project_title, description=f"{project_title} - 由 VibeCopilot 自动管理", auto_create=True
                    )

                    if not ensure_result.get("success") or not ensure_result.get("project"):
                        console_utils.print_error(f"无法确保远程 GitHub Project '{project_title}' 的状态: {ensure_result.get('message')}")
                        console_utils.print_info("请检查 GitHub CLI 认证、网络连接以及 .env 中的 GITHUB_TOKEN 和 GITHUB_OWNER/REPO 配置。")
                        return 1

                    remote_project_info = ensure_result["project"]
                    remote_project_node_id = remote_project_info["id"]
                    remote_project_number = remote_project_info["number"]
                    remote_project_title = remote_project_info["title"]
                    console_utils.print_success(
                        f"远程 GitHub Project '{remote_project_title}' (ID: {remote_project_node_id}, Number: {remote_project_number}) 已就绪。"
                    )

                # 步骤3: 在本地查找关联的roadmap或根据标题查找
                existing_local_roadmap_id = roadmap_service.find_roadmap_by_github_link(
                    owner=github_owner, repo=github_repo, project_identifier=remote_project_node_id
                )

                # 如果通过映射关系未找到，尝试通过标题查找
                if not existing_local_roadmap_id:
                    logger.info(f"通过GitHub链接未找到roadmap，尝试通过标题'{remote_project_title}'查找")
                    local_roadmap_by_title = roadmap_service.get_roadmap_by_title(remote_project_title)
                    if local_roadmap_by_title:
                        existing_local_roadmap_id = local_roadmap_by_title.get("id")
                        logger.info(f"通过标题'{remote_project_title}'找到本地roadmap ID: {existing_local_roadmap_id}")

                # 步骤4: 处理已有或创建新的roadmap
                new_local_roadmap_id = None

                if existing_local_roadmap_id:
                    new_local_roadmap_id = existing_local_roadmap_id
                    console_utils.print_info(f"找到现有本地 Roadmap (ID: {new_local_roadmap_id})，将确保其与远程 Project 关联。")
                else:
                    # 如果不存在，创建新的本地Roadmap
                    console_utils.print_info(f"正在创建本地 Roadmap: '{remote_project_title}'...")
                    create_roadmap_result = roadmap_service.create_roadmap(
                        title=remote_project_title,
                        description=f"本地 Roadmap，关联到 GitHub Project '{remote_project_title}' (ID: {remote_project_node_id})",
                    )

                    if create_roadmap_result.get("success"):
                        new_local_roadmap_id = create_roadmap_result.get("roadmap_id")
                        console_utils.print_success(f"本地 Roadmap '{remote_project_title}' (ID: {new_local_roadmap_id}) 创建成功。")
                    else:
                        console_utils.print_error(f"创建本地 Roadmap '{remote_project_title}' 失败: {create_roadmap_result.get('error')}")

                # 步骤5: 链接roadmap到GitHub项目并设置为活动roadmap
                if new_local_roadmap_id:
                    # 链接本地Roadmap到远程GitHub Project
                    console_utils.print_info(f"正在关联本地 Roadmap (ID: {new_local_roadmap_id}) 与远程 GitHub Project '{remote_project_title}'...")
                    link_result = roadmap_service.link_roadmap_to_github_project(
                        local_roadmap_id=new_local_roadmap_id,
                        github_owner=github_owner,
                        github_repo=github_repo,
                        github_project_identifier=remote_project_node_id,
                    )

                    if link_result.get("success"):
                        console_utils.print_success("本地 Roadmap 与远程 GitHub Project 关联成功。")

                        # 设置为活动roadmap
                        console_utils.print_info(f"正在将 Roadmap (ID: {new_local_roadmap_id}) 设为活动状态...")
                        switch_result = roadmap_service.switch_roadmap(new_local_roadmap_id)

                        if switch_result.get("success"):
                            console_utils.print_success(f"Roadmap '{remote_project_title}' (ID: {new_local_roadmap_id}) 已设为活动状态。")
                        else:
                            console_utils.print_error(f"切换到 Roadmap (ID: {new_local_roadmap_id}) 失败: {switch_result.get('message')}")
                    else:
                        console_utils.print_error(f"关联本地 Roadmap (ID: {new_local_roadmap_id}) 与远程 Project 失败: {link_result.get('message')}")

                console.print("[bold yellow]GitHub Project 和本地 Roadmap 处理完成。[/bold yellow]")

            except Exception as e:
                logger.error(f"处理 GitHub Project 和本地 Roadmap 关联时出错: {e}", exc_info=True)
                console_utils.print_error(f"处理 GitHub Project 和本地 Roadmap 关联时出错: {e}")
        elif not is_github_settings_configured:
            console_utils.print_warning("GitHub 未配置 (缺少 owner 或 repo)，跳过 GitHub Project 和本地 Roadmap 处理。")
            console_utils.print_info("请在 settings.json 或通过环境变量 GITHUB_OWNER/GITHUB_REPO 进行配置，然后重新运行 init。")
        elif not is_github_cli_authenticated:
            console_utils.print_warning("GitHub CLI 未认证，跳过 GitHub Project 和本地 Roadmap 处理。")
            console_utils.print_info("请运行 'gh auth login' 并确保 GITHUB_TOKEN 已设置。")

        # 最终总结
        if is_vibecopilot_project:
            console_utils.print_success("🚀 VibeCopilot项目自举初始化完成！")
        else:
            console_utils.print_success(f"🚀 项目 {project_state.get_project_name()} 的VibeCopilot环境初始化完成！")
        console_utils.print_info("运行 'vc status show' 查看项目状态，或 'vc roadmap list' 查看路线图。")

        if verbose and format == "json":
            # 需要重新构造一个包含所有更新信息的 result 对象
            # 为简化，暂时不在此处重新生成完整的 JSON output
            pass
            # output_result(result, format, "generic", verbose)
        return 0
    else:
        console_utils.print_error(f"初始化失败: {result.get('error', '未知错误')}")
        return 1


def _ask_project_info(console, result):
    """交互式询问并设置项目基本信息 (名称、阶段) 和 GitHub 仓库配置。"""
    try:
        status_service = StatusService.get_instance()
        project_state = status_service.project_state

        # 获取现有项目名称
        current_name = project_state.get_project_name()
        is_unnamed = current_name == "未设置" or not current_name

        # 获取现有项目阶段
        current_phase = project_state.get_current_phase()
        is_unphased = current_phase == "未设置" or not current_phase

        # 这些是从初始检查结果中获取的，用于决定是否可以进行 GitHub 交互
        github_enabled = result.get("checks", {}).get("integrations", {}).get("github", {}).get("enabled", False)
        github_configured = (
            result.get("checks", {}).get("integrations", {}).get("github", {}).get("configured", False)
        )  # Configured based on owner/repo in settings.json
        github_authenticated = result.get("checks", {}).get("integrations", {}).get("github", {}).get("authenticated", False)

        project_name_to_use = current_name
        if is_unnamed:
            if Confirm.ask("项目名称未设置或为空，是否现在设置？", default=True):
                project_name_input = click.prompt("请输入项目名称", type=str, default=os.path.basename(os.getcwd()))
                if project_name_input:
                    project_state.set_project_name(project_name_input)
                    project_name_to_use = project_name_input
                    console_utils.print_success(f"已设置项目名称为: {project_name_to_use}")
                else:
                    project_name_to_use = os.path.basename(os.getcwd())  # Fallback if user enters empty
                    project_state.set_project_name(project_name_to_use)  # Save fallback
                    console_utils.print_info(f"项目名称设置为空，将使用默认名称: {project_name_to_use}")
            else:
                # 用户选择不设置，使用默认值并保存
                project_name_to_use = os.path.basename(os.getcwd())
                if project_state.get_project_name() != project_name_to_use:  # 避免不必要的写操作
                    project_state.set_project_name(project_name_to_use)
                console_utils.print_info(f"项目名称未设置，将使用默认名称: {project_name_to_use}")

        if is_unphased:
            if Confirm.ask("项目阶段未设置或为空，是否现在设置？", default=True):
                phases = ["规划", "开发", "测试", "发布", "维护"]
                phase_input = click.prompt("请选择项目阶段", type=click.Choice(phases), default="规划", show_choices=True)
                project_state.set_current_phase(phase_input)
                console_utils.print_success(f"已设置项目阶段为: {phase_input}")
            else:
                # 用户选择不设置，使用默认值并保存
                default_phase = "规划"
                if project_state.get_current_phase() != default_phase:  # 避免不必要的写操作
                    project_state.set_current_phase(default_phase)
                console_utils.print_info(f"项目阶段未设置，将使用默认阶段: {default_phase}")

        # 配置GitHub仓库信息 (owner/repo in settings.json)
        # _configure_github_settings 负责与用户交互并保存到 settings.json
        # 它应该在 _ask_project_info 之前或独立调用，因为它影响 github_configured 状态
        # 这里假设 _configure_github_settings 已经被调用过了，或者它的逻辑是独立的。
        # 为了安全，我们可以在 init_command 的主流程中确保 _configure_github_settings 在这之前被调用。

        # GitHub Project 关联逻辑已移至 init_command 主流程
        # 不再在此函数中调用 github_sync.ensure_github_project() 或 github_sync.save_project_to_config()

        logger.info(f"_ask_project_info完成。项目名: {project_state.get_project_name()}, 阶段: {project_state.get_current_phase()}")

    except Exception as e:
        logger.error(f"设置项目信息时出错: {e}", exc_info=True)
        console_utils.print_error(f"设置项目信息时出错: {e}")


def _configure_github_settings(console, status_service, github_enabled, github_configured, github_authenticated):
    """配置GitHub设置"""
    # 如果环境变量中已经配置了GitHub信息，直接保存到settings.json
    if os.environ.get("GITHUB_OWNER") and os.environ.get("GITHUB_REPO"):
        env_owner = os.environ.get("GITHUB_OWNER")
        env_repo = os.environ.get("GITHUB_REPO")
        env_project_title = os.environ.get("ROADMAP_PROJECT_NAME")  # 新增：读取环境变量
        console_utils.print_info(f"已从环境变量检测到GitHub配置: {env_owner}/{env_repo}")
        if env_project_title:
            console_utils.print_info(f"环境变量中的 ROADMAP_PROJECT_NAME: {env_project_title}")

        github_config = {
            "owner": env_owner,
            "repo": env_repo,
        }
        if env_project_title:  # 新增：如果存在则添加到配置中
            github_config["project_title"] = env_project_title

        update_success = status_service.update_settings("github_info", github_config)

        if update_success:
            console_utils.print_success(f"已将环境变量中的GitHub配置保存到settings.json")
        else:
            console_utils.print_error("保存配置失败，请查看日志")
        return

    # 检查现有的settings.json配置
    # github_info 应该从 StatusService 获取，它会读取 settings.json
    # github_settings_from_file = status_service.load_settings_json().get("github_info", {})
    github_settings_from_file = status_service.get_settings_value("github_info", {})

    # 如果已经有有效配置，询问是否需要更新
    # configured 应该基于 owner 和 repo 是否存在来判断
    has_owner_repo_config = github_settings_from_file.get("owner") and github_settings_from_file.get("repo")

    if has_owner_repo_config:
        owner = github_settings_from_file.get("owner")
        repo = github_settings_from_file.get("repo")
        console_utils.print_info(f"当前GitHub配置 (来自 settings.json): {owner}/{repo}")

        if not Confirm.ask("是否需要更新GitHub配置？"):
            return

    # 尝试从Git检测获取默认建议值 (这部分依赖 GitHubInfoProvider, 它可能需要调整)
    # 我们先假设它可以提供 detected_owner 和 detected_repo
    # 为了简化，暂时直接使用 status_service.get_domain_status("github_info")
    # 但长远看，GitHubInfoProvider 也应该只关注 settings.json 的内容
    github_domain_info = status_service.get_domain_status("github_info")
    detected_owner = github_domain_info.get("detected_owner")
    detected_repo = github_domain_info.get("detected_repo")

    # 询问用户配置GitHub信息
    console_utils.print_info("请配置GitHub仓库信息:")

    # 输入owner
    default_owner_val = detected_owner or github_settings_from_file.get("owner") or ""
    prompt_text = "GitHub用户名或组织名"
    if default_owner_val:
        prompt_text += f" [建议: {default_owner_val}]"
    owner_input = click.prompt(prompt_text, type=str, default=default_owner_val, show_default=bool(default_owner_val))

    # 输入repo
    default_repo_val = detected_repo or github_settings_from_file.get("repo") or ""

    # 确定 project_title 的默认提示值
    # 优先级: settings.json中的project_title -> ROADMAP_PROJECT_NAME环境变量 -> project_state中的项目名 -> 当前目录名
    default_project_title_val = github_settings_from_file.get("project_title")
    if not default_project_title_val:
        default_project_title_val = os.getenv("ROADMAP_PROJECT_NAME")
    if not default_project_title_val:
        # 需要 StatusService 的 project_state 实例来获取项目名
        # 这个调用可能需要在 _configure_github_settings 外部确保 project_state 已基本设置
        current_project_name_from_state = status_service.project_state.get_project_name()
        if current_project_name_from_state and current_project_name_from_state != "未设置" and current_project_name_from_state != "VibeCopilot":
            default_project_title_val = current_project_name_from_state
    if not default_project_title_val:  # 最后的默认
        default_project_title_val = os.path.basename(os.getcwd())

    prompt_text_repo = "GitHub仓库名称"
    if default_repo_val:
        prompt_text_repo += f" [建议: {default_repo_val}]"
    repo_input = click.prompt(prompt_text_repo, type=str, default=default_repo_val, show_default=bool(default_repo_val))

    # 新增：交互式询问 project_title，如果 settings.json 中没有的话
    project_title_input = click.prompt("GitHub项目标题", type=str, default=default_project_title_val, show_default=True)

    if owner_input and repo_input:
        github_config_to_save = {
            "owner": owner_input,
            "repo": repo_input,
        }
        if project_title_input:  # 新增：保存 project_title
            github_config_to_save["project_title"] = project_title_input

        logger.info(f"准备保存GitHub配置到 settings.json: {github_config_to_save}")

        try:
            if not status_service.settings_path.parent.exists():
                status_service.settings_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建了配置目录: {status_service.settings_path.parent}")

            # current_settings = status_service.load_settings_json() # Incorrect method
            # Get current settings from the service instance's loaded config
            # current_settings = status_service.settings_config.copy() # Load from memory, use copy
            current_settings = status_service.settings_manager._config.copy()  # Load from memory, use copy
            current_settings["github_info"] = github_config_to_save

            # 使用 StatusService 的 update_settings 方法来更新和保存
            save_success = status_service.update_settings("github_info", github_config_to_save)

            if save_success:
                logger.info("成功保存GitHub配置到settings.json")
                console_utils.print_success(f"已保存GitHub配置: {owner_input}/{repo_input}")
                console.print(f"[bold green]✓ GitHub 配置已更新并保存到 '{status_service.settings_path}'.[/bold green]")

                logger.info("GitHub配置已保存，路线图关联将在init_command函数中处理")
            else:
                # 这个else分支可能永远不会到达，因为save_settings_json在失败时会记录错误并返回None或False
                logger.error("保存settings.json配置失败 (save_settings_json 返回非True值)")
                console_utils.print_error("保存GitHub配置失败。")

        except Exception as e:
            logger.error(f"保存settings.json配置失败: {e}", exc_info=True)
            console_utils.print_error(f"保存settings.json配置失败: {e}. 请检查文件权限或路径。")
    else:
        console_utils.print_warning("未提供完整的 GitHub owner 和 repo 信息，配置未保存。")

    # 这部分逻辑与 settings.json 无关，可以保留
    # if not github_enabled or not github_configured: # 检查原始的 result 状态
    #     console_utils.print_warning(f"GitHub集成未完全配置，缺少环境变量或认证。")
    #     console_utils.print_info("请在.env文件中设置 GITHUB_OWNER, GITHUB_REPO (可选) 和 GITHUB_TOKEN 以启用完整的GitHub项目同步功能。")
    # elif not github_authenticated:
    #      console_utils.print_warning("GitHub CLI 未认证。请运行 'gh auth login'。")

    # 提示用户在.env中设置GitHub token (这个检查总是相关的)
    if not os.environ.get("GITHUB_TOKEN"):
        console_utils.print_warning("未检测到GitHub Token环境变量 (GITHUB_TOKEN)")
        console_utils.print_info("请在.env文件中添加以下行:")
        console_utils.print_info("GITHUB_TOKEN=your_personal_access_token")
        console_utils.print_info("可以在 https://github.com/settings/tokens 创建新token (确保有 'project' 权限)")
