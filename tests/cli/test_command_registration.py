"""
测试命令注册完整性

验证command-list.md中定义的所有命令是否都已正确注册到CLI工具中
"""

import json
import os
import sys
from pathlib import Path

import pytest

# 移到顶部
from src.cli.main import get_cli_app  # 假设这是获取CLI应用的函数

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 从command-list.md中定义的所有顶级命令
EXPECTED_TOP_LEVEL_COMMANDS = {
    "rule": "规则管理命令",
    "flow": "工作流定义管理命令",
    "task": "任务管理命令",
    "status": "项目状态管理命令",
    "memory": "知识库管理命令",
    "db": "数据库管理命令",
    "help": "帮助命令",
    "roadmap": "路线图管理命令",
}

# 子命令映射
EXPECTED_SUBCOMMANDS = {
    "rule": ["list", "show", "create", "update", "delete", "validate", "export", "import"],
    "flow": [
        "list",
        "show",
        "create",
        "update",
        "export",
        "import",
        "run",
        "context",
        "next",
        "visualize",
    ],
    "flow session": ["list", "show", "create", "pause", "resume", "abort", "delete"],
    "roadmap": ["list", "show", "create", "update", "delete", "sync", "switch", "status"],
    "task": ["list", "show", "create", "update", "delete", "link", "comment"],
    "status": ["show", "flow", "roadmap", "task", "update", "init"],
    "memory": ["list", "show", "create", "update", "delete", "search", "import", "export", "sync"],
    "db": ["init", "list", "show", "create", "update", "delete", "query", "backup", "restore"],
}


def get_registered_commands():
    """获取当前已注册的所有命令"""
    app = get_cli_app()
    return {cmd.name: cmd.help for cmd in app.commands}


def get_registered_subcommands(command):
    """获取指定命令的所有已注册子命令"""
    app = get_cli_app()
    cmd = app.get_command(None, command)
    if cmd is None:
        return []
    return [subcmd.name for subcmd in cmd.commands.values()]


@pytest.mark.parametrize("command, description", EXPECTED_TOP_LEVEL_COMMANDS.items())
def test_top_level_command_registration(command, description):
    """测试顶级命令是否都已正确注册"""
    registered_commands = get_registered_commands()
    assert command in registered_commands, f"命令 '{command}' 未注册"
    # 可选：检查命令描述是否匹配
    # assert registered_commands[command] == description, f"命令 '{command}' 的描述不匹配"


@pytest.mark.parametrize("command, expected_subs", EXPECTED_SUBCOMMANDS.items())
def test_subcommand_registration(command, expected_subs):
    """测试子命令是否都已正确注册"""
    if " " in command:  # 处理多级命令，如 'flow session'
        parent, child = command.split(" ")
        registered_subs = get_registered_subcommands(parent)
        assert child in registered_subs, f"子命令组 '{command}' 未注册"
        registered_subsubs = get_registered_subcommands(f"{parent} {child}")
    else:
        registered_subs = get_registered_subcommands(command)

    for subcmd in expected_subs:
        assert subcmd in registered_subs, f"命令 '{command}' 的子命令 '{subcmd}' 未注册"


def test_command_help_availability():
    """测试所有命令是否都有帮助信息"""
    app = get_cli_app()
    for command in EXPECTED_TOP_LEVEL_COMMANDS:
        cmd = app.get_command(None, command)
        assert cmd is not None, f"命令 '{command}' 不存在"
        assert cmd.help is not None, f"命令 '{command}' 没有帮助信息"


def test_command_execution_basic():
    """测试所有命令是否能基本执行（返回帮助信息而不是错误）"""
    app = get_cli_app()
    runner = app.test_cli_runner()

    for command in EXPECTED_TOP_LEVEL_COMMANDS:
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0, f"命令 '{command} --help' 执行失败: {result.output}"


if __name__ == "__main__":
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(project_root)
    pytest.main([__file__, "-v"])
