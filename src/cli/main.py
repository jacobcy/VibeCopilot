#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
支持子命令的延迟加载，提高启动性能。
"""

import logging
import os
import re
import sys
from importlib import import_module
from pathlib import Path
from typing import Callable, Dict, Union

import click
from rich.console import Console

# 确保在所有其他导入前加载.env文件
try:
    from dotenv import load_dotenv

    # 尝试查找项目根目录的.env文件
    project_root = Path(__file__).resolve().parent.parent.parent  # 假设当前文件在src/cli目录
    dotenv_path = project_root / ".env"

    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        print(f"已加载环境变量: {dotenv_path}")
    else:
        # 尝试在当前目录加载
        load_dotenv(override=True)
        print("尝试从当前目录加载环境变量")
except ImportError:
    print("警告: python-dotenv未安装，无法自动加载.env文件")
except Exception as e:
    print(f"加载环境变量时出错: {e}")

# 设置默认日志级别为WARNING
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()], force=True  # 强制重新配置日志
)

logger = logging.getLogger(__name__)

# 立即导入帮助命令
from src.cli.commands.help.help_click import help as help_command

# Import console utils
from src.utils.console_utils import print_error, print_info

# 命令分组（用于帮助显示）
COMMAND_GROUPS = {"基础命令": ["help", "status"], "开发工具": ["rule", "flow", "template"], "数据管理": ["db", "memory"], "项目管理": ["roadmap", "task"]}

# 子命令模块映射
COMMAND_MODULES = {
    "status": "src.cli.commands.status.status_click:status",
    "rule": "src.cli.commands.rule.rule_click:rule",
    "roadmap": "src.cli.commands.roadmap.roadmap_click:roadmap",
    "db": "src.cli.commands.db.db_click:db",
    "flow": "src.cli.commands.flow.flow_click:flow",
    "memory": "src.cli.commands.memory.memory_click:memory",
    "template": "src.cli.commands.template.template_click:template",
    "task": "src.cli.commands.task.task_click:task",
}

# 预加载的命令
PRELOADED_COMMANDS = {"help": help_command}


class LazyLoadingGroup(click.Group):
    """
    延迟加载命令组类

    在显示帮助信息时预加载子命令，保持延迟加载的性能优势
    同时解决帮助信息不一致的问题
    """

    def __init__(self, name, module_path, help=None, **attrs):
        self.module_path = module_path
        self._loaded_command = None
        self._loaded = False
        super().__init__(name=name, callback=None, help=help, **attrs)

    def _load_command(self):
        """
        加载实际的命令实现
        """
        if not self._loaded:
            try:
                logger.debug(f"LazyLoadingGroup: Attempting to load module {self.module_path}")
                module_name, attribute = self.module_path.split(":")
                module = import_module(module_name)
                self._loaded_command = getattr(module, attribute)
                self._loaded = True
                logger.debug(f"LazyLoadingGroup: Successfully loaded {attribute} from {module_name}")
            except Exception as e:
                logger.error(f"加载命令模块失败 {self.module_path}: {e}", exc_info=True)
                raise click.ClickException(f"加载命令失败: {str(e)}")
        return self._loaded_command

    def get_command(self, ctx, cmd_name):
        """
        获取子命令，预加载实际命令以显示完整的子命令
        """
        try:
            # 尝试加载实际命令并获取其子命令
            cmd = self._load_command()
            return cmd.get_command(ctx, cmd_name)
        except Exception as e:
            # 如果加载失败，回退到基本子命令
            logger.warning(f"获取命令 {self.name} 的子命令 {cmd_name} 失败: {e}")
            return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        """
        列出所有子命令，预加载实际命令以显示完整的子命令列表
        """
        try:
            # 尝试加载实际命令并获取其子命令列表
            cmd = self._load_command()
            return cmd.list_commands(ctx)
        except Exception as e:
            # 如果加载失败，回退到基本子命令列表
            logger.warning(f"获取命令 {self.name} 的子命令列表失败: {e}")
            return super().list_commands(ctx)

    def invoke(self, ctx):
        """
        调用命令，预加载实际命令并调用其回调函数
        """
        if ctx.protected_args:
            # 如果有子命令，则正常调用
            return super().invoke(ctx)
        else:
            # 如果没有子命令，则加载实际命令并调用其回调函数
            try:
                cmd = self._load_command()
                if cmd.callback is not None:
                    return cmd.callback(**ctx.params)
            except Exception as e:
                logger.error(f"调用命令 {self.name} 失败: {e}")
            # 如果加载失败或没有回调函数，则正常调用
            return super().invoke(ctx)

    def get_help(self, ctx):
        """
        获取帮助信息，预加载实际命令以显示完整的帮助
        """
        try:
            # 尝试加载实际命令并获取其帮助信息
            cmd = self._load_command()
            return cmd.get_help(ctx)
        except Exception as e:
            # 如果加载失败，回退到基本帮助信息
            logger.warning(f"获取命令 {self.name} 的帮助信息失败: {e}")
            return super().get_help(ctx)


def load_command(module_path: str) -> click.Command:
    """
    延迟加载命令模块

    Args:
        module_path: 模块路径，格式为 "package.module:attribute"

    Returns:
        click.Command: 加载的命令对象
    """
    try:
        module_name, attribute = module_path.split(":")
        module = import_module(module_name)
        return getattr(module, attribute)
    except Exception as e:
        logger.error(f"加载命令模块失败 {module_path}: {e}")
        raise click.ClickException(f"加载命令失败: {str(e)}")


def set_log_level(verbose: bool):
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.getLogger().setLevel(log_level)
    logging.getLogger("src").setLevel(log_level)
    if verbose:
        logger.debug("Verbose logging enabled via set_log_level")


def set_log_level_callback(ctx, param, value):
    actual_verbose_value = False
    if "-v" in sys.argv or "--verbose" in sys.argv:
        logger.debug("set_log_level_callback: -v or --verbose found in sys.argv. Setting verbose to True.")
        actual_verbose_value = True
    else:
        logger.debug("set_log_level_callback: -v or --verbose NOT found in sys.argv. Using callback value or default False.")
        actual_verbose_value = value

    set_log_level(actual_verbose_value)

    if ctx.obj is None:
        ctx.obj = {}
    if isinstance(ctx.obj, dict):
        ctx.obj["verbose_set_by_callback"] = actual_verbose_value

    return actual_verbose_value


def initialize_status_module():
    """初始化状态模块

    此函数应该在日志级别设置后调用，确保状态模块的日志输出受CLI参数控制
    """
    try:
        logger.info("初始化状态模块...")
        # 惰性导入，确保只在需要时加载状态模块
        from src.status import initialize as init_status

        init_status()
        logger.info("状态模块初始化完成")
    except Exception as e:
        logger.error(f"状态模块初始化失败: {e}")


# 将 CLIContext 类定义移到模块顶部
class CLIContext:
    """CLI上下文对象，用于在命令间传递服务实例和其他信息"""

    def __init__(self, verbose: bool, roadmap_service, status_service):
        self.verbose = verbose
        self.roadmap_service = roadmap_service
        self.status_service = status_service
        # ... 添加其他服务实例属性


def get_cli_app():
    """获取CLI应用实例"""

    # 将 print_version 函数定义移到这里
    def print_version(ctx, param, value):
        """打印版本信息"""
        if not value or ctx.resilient_parsing:
            return
        from src import __version__

        # Use print_info for user-facing version info
        print_info(f"VibeCopilot version: {__version__}", title="Version")
        ctx.exit()

    @click.group(help="VibeCopilot CLI工具", context_settings={"help_option_names": ["-h", "--help"]})
    @click.option("--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="显示版本信息")
    # 修改 --verbose 选项，添加 is_eager=True 和 callback
    @click.option("--verbose", "-v", is_flag=True, is_eager=True, callback=set_log_level_callback, help="显示详细日志信息")
    @click.pass_context
    def cli(ctx, verbose):
        """VibeCopilot 命令行工具

        VibeCopilot是一个AI辅助开发工具，提供以下功能：

        1. 规则命令(/command): 由AI助手直接处理的简单交互命令
        2. 程序命令(//command): 转换为CLI执行的复杂持久化命令

        命令分组:
          基础命令:
            help     显示帮助信息
            status   项目状态管理命令

          开发工具:
            rule     规则管理命令
            flow     工作流管理命令
            template 模板管理命令

          数据管理:
            db      数据库管理命令
            memory  知识库管理命令

          项目管理:
            roadmap 路线图管理命令
            task    任务管理命令

        使用 'vc COMMAND --help' 查看具体命令的帮助信息
        """
        # 在 Click 解析完参数后，将正确的 verbose 值设置到 ctx.obj 上
        # 确保 ctx.obj 是 CLIContext 实例
        if isinstance(ctx.obj, CLIContext):
            ctx.obj.verbose = verbose  # 将解析到的 verbose 值赋给上下文对象
            logger.debug(f"CLI command group callback received verbose: {verbose}")
        else:
            logger.warning(f"ctx.obj is not a CLIContext instance, cannot set verbose property. Type: {type(ctx.obj)}")

        # 如果没有子命令，显示帮助信息
        if ctx.invoked_subcommand is None:
            # click.echo is standard for help output, keep it
            click.echo(ctx.get_help())

    # 首先注册预加载的命令
    for cmd_name, cmd in PRELOADED_COMMANDS.items():
        cli.add_command(cmd)

    # 从help_click.py导入命令描述信息
    from src.cli.commands.help.help_click import COMMAND_GROUPS as HELP_COMMAND_GROUPS

    # 动态注册其他命令
    for cmd_name, module_path in COMMAND_MODULES.items():
        # 获取命令描述
        cmd_description = None
        for group in HELP_COMMAND_GROUPS.values():
            if cmd_name in group:
                cmd_description = group[cmd_name]["description"]
                break

        # 创建延迟加载的命令组
        cmd = LazyLoadingGroup(cmd_name, module_path, help=cmd_description or f"加载并执行 {cmd_name} 命令")

        cli.add_command(cmd)

    return cli


def print_error_message(command: str):
    """打印错误信息"""
    # Use print_error for error message
    print_error(f"未知命令: {command}", title="命令错误")

    # Keep direct console print for structured help for now
    # Consider using print_table or formatted print_info later
    console = Console()  # Re-create console instance locally if needed for specific formatting
    console.print("\n可用命令:")

    for group, commands in COMMAND_GROUPS.items():
        console.print(f"\n[bold]{group}[/bold]")
        for cmd in commands:
            console.print(f"  {cmd}")

    console.print("\n使用 [bold]vibecopilot --help[/bold] 查看详细帮助信息")


def main():
    """CLI主入口"""
    logger.info("CLI main() function started.")

    # === 在这里解析基本的命令行参数，以便在初始化服务前设置日志级别等 ===
    # 移除早期解析 verbose 的复杂逻辑
    # set_log_level(verbose) # 这行也不需要了，在 Click callback 中处理
    # === 早期参数解析结束 ===

    # 设置日志级别 - 应在加载环境变量后，确保环境变量中的LOG_LEVEL生效
    # 由于日志配置是集中在 config/logging.yaml 中，并通过 src.core.log_init 初始化
    # 这里只需要设置根 logger 的级别即可，更详细的日志配置应在初始化时处理
    # Log level will now be set by the --verbose callback during click invocation

    # === 将环境变量加载移到这里 === (已存在，保留)
    try:
        from dotenv import load_dotenv

        # 尝试查找项目根目录的.env文件
        project_root = Path(__file__).resolve().parent.parent.parent  # 假设当前文件在src/cli目录
        dotenv_path = project_root / ".env"

        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path, override=True)
            logger.info(f"已加载环境变量: {dotenv_path}")
        else:
            # 尝试在当前目录加载
            load_dotenv(override=True)
            logger.info("尝试从当前目录加载环境变量")
    except ImportError:
        logger.warning("警告: python-dotenv未安装，无法自动加载.env文件")
    except Exception as e:
        logger.error(f"加载环境变量时出错: {e}")
    # === 环境变量加载结束 ===

    # 预准备数据库 - 确保在服务初始化前完成
    try:
        logger.info("确保数据库存在...")
        from src.db.connection_manager import ensure_tables_exist

        # TODO: 根据配置决定是否强制重建
        ensure_tables_exist(force_recreate=False)
        logger.info("数据库检查/创建完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print_error(f"数据库初始化失败: {e}", title="数据库错误")
        # 数据库是核心依赖，初始化失败通常需要退出
        sys.exit(1)

    # === 初始化所有核心服务并创建上下文对象 ===
    roadmap_service_instance = None
    status_service_instance = None
    ctx_obj_instance = None

    try:
        logger.info("Initializing core services...")
        from src.roadmap.service import RoadmapService
        from src.status.service import StatusService

        logger.debug("main() - Attempting to instantiate RoadmapService...")
        roadmap_service_instance = RoadmapService()
        logger.debug(f"main() - RoadmapService instantiated: {roadmap_service_instance}")

        logger.debug("main() - Attempting to get StatusService instance...")
        status_service_instance = StatusService.get_instance()
        logger.debug(f"main() - StatusService instance obtained: {status_service_instance}")

        logger.debug("main() - Attempting to create CLIContext...")
        ctx_obj_instance = CLIContext(False, roadmap_service_instance, status_service_instance)
        logger.debug(f"main() - CLIContext object created: {ctx_obj_instance}")

    except Exception as e_main_service_init:
        logger.critical(f"CRITICAL ERROR during core service initialization: {e_main_service_init}", exc_info=True)
        print_error(f"核心服务初始化失败: {e_main_service_init}", title="服务错误")
        sys.exit(1)
    # === 服务初始化完成 ===

    # 获取CLI应用 - 现在 cli() 函数将接收一个 CLIContext 实例
    cli_app = get_cli_app()

    # 在执行命令前尝试初始化状态模块 (已存在，保留)
    # === 将状态模块初始化移到这里 ===
    # 确保状态模块初始化在日志级别设置后进行
    try:
        logger.info("初始化状态模块...")
        # 惰性导入，确保只在需要时加载状态模块
        from src.status import initialize as init_status

        init_status()
        logger.info("状态模块初始化完成")
    except Exception as e:
        logger.error(f"状态模块初始化失败: {e}")
        # 状态模块初始化失败不一定是致命错误，记录日志后继续尝试执行命令
    # === 状态模块初始化结束 ===

    # 执行CLI命令 - 现在 cli() 及其子命令的 @click.pass_obj 将接收 ctx_obj_instance
    try:
        # 执行根上下文的 invoke 方法，将完整的命令行参数传递给它
        # Click 会根据定义的命令和选项解析这些参数，并调用相应的回调
        logger.debug(f"开始执行CLI命令: vibecopilot {' '.join(sys.argv[1:])}")
        # 使用Click的标准方式运行应用
        # prog_name 设置为 'vibecopilot' 以确保帮助信息中的程序名称正确
        # args 从 sys.argv[1:] 获取，obj 传递已初始化的上下文
        # cli_app.main() 会处理 SystemExit，所以我们可以直接返回其结果或让它自行退出
        # standalone_mode=True (默认) 使其行为像一个独立的脚本入口。
        cli_app.main(args=sys.argv[1:], obj=ctx_obj_instance, prog_name="vibecopilot", standalone_mode=True)
        # 由于 standalone_mode=True 会导致 sys.exit, 通常这里之后的代码不会执行，除非 Click 的 main 捕获了 SystemExit 且没重抛
        # 为了确保 main 函数有返回值给外层的 sys.exit(main())，如果 Click 的 main 正常结束（例如显示帮助并退出），
        # 它可能会抛出 SystemExit(0)。如果发生错误，可能是 SystemExit(1) 或其他。
        # 如果 cli_app.main 因为 standalone_mode=True 自己处理了退出，那么这里的 return 0 可能不会被达到。
        # 但如果它返回了，我们假设是成功。
        return 0

    except click.exceptions.NoSuchOption as e:
        # Use print_error for invalid option message
        error_msg = f"无效的选项: {e.option_name}\\n使用 'vibecopilot {e.ctx.command.name} --help' 查看有效的选项"
        print_error(error_msg, title="选项错误")
        return 1
    except click.exceptions.UsageError as e:
        if "No such command" in str(e):
            # Assuming the command is the first argument after 'vibecopilot'
            try:
                # This part might need adjustment depending on how click handles argv in this invoke setup
                # For now, keep the original logic for message generation
                command_name_arg_index = sys.argv.index("vibecopilot") + 1
                if command_name_arg_index < len(sys.argv):
                    command = sys.argv[command_name_arg_index]
                else:
                    command = "未知命令"
            except ValueError:
                match = re.search(r"No such command '(.+)'", str(e))
                command = match.group(1) if match else "未知命令"

            print_error_message(command)  # This already uses print_error
        else:
            # Use print_error for other usage errors
            print_error(str(e), title="使用错误")
        return 1
    except SystemExit as e:  # Click 用 SystemExit 来退出，例如显示帮助后
        # 如果 Click 因为 standalone_mode=True 而调用了 sys.exit()，这个异常会被捕获。
        # 我们可以根据 e.code 决定 main() 的返回值。
        # logger.debug(f"CLI 通过 SystemExit 退出，代码: {e.code}")
        # 如果不在这里 sys.exit(e.code)，那么外层的 sys.exit(main()) 会执行。
        # 所以这里可以简单地重抛，或者让 main 函数返回 e.code。
        # 为了让外层的 sys.exit(main()) 工作，我们返回 e.code。
        # 如果 e.code 是 None（例如直接调用 exit()），则默认为0。
        return e.code if e.code is not None else 0
    except Exception as e:
        # Use logger.exception to print traceback
        logger.exception("命令执行出错")
        # Use print_error for general execution errors
        print_error(str(e), title="执行错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())
