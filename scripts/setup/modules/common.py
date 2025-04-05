#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数和常量定义模块。
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()

# 操作系统类型
OS_TYPE = platform.system()
IS_WINDOWS = OS_TYPE == "Windows"
IS_MACOS = OS_TYPE == "Darwin"
IS_LINUX = OS_TYPE == "Linux"


# Python路径(根据平台设置)
def get_python_path():
    """根据平台获取Python路径"""
    if IS_MACOS:
        return "/opt/homebrew/opt/python@3.13/bin/python3"
    elif IS_LINUX:
        return "/usr/bin/python3"
    elif IS_WINDOWS:
        return "python"
    return sys.executable


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """执行Shell命令并返回结果."""
    process = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    return process.returncode, process.stdout


def get_shell_config_file() -> tuple[bool, Path]:
    """获取当前shell的配置文件路径."""
    if IS_WINDOWS:
        return False, Path()

    home = Path.home()
    shell = os.environ.get("SHELL", "")

    if "zsh" in shell:
        config_file = home / ".zshrc"
    elif "bash" in shell:
        config_file = home / ".bashrc"
    else:
        return False, Path()

    return config_file.exists(), config_file


def update_shell_path(path_to_add: str) -> None:
    """更新shell配置文件，将指定路径添加到PATH变量."""
    if IS_WINDOWS:
        print(f"Windows系统请手动添加以下路径到环境变量PATH: {path_to_add}")
        return

    exists, config_file = get_shell_config_file()
    if not exists:
        print(f"未找到shell配置文件，请手动添加以下内容到您的shell配置中:")
        print(f'export PATH="$PATH:{path_to_add}"')
        return

    # 读取配置文件
    content = config_file.read_text()
    path_addition = f'export PATH="$PATH:{path_to_add}"'

    # 检查是否已存在
    if path_to_add in content:
        print(f"PATH配置已存在于{config_file}")
        return

    # 添加PATH配置
    with open(config_file, "a") as f:
        f.write(f"\n# Added by VibeCopilot setup\n{path_addition}\n")

    print(f"已更新{config_file}，添加了{path_to_add}到PATH")
    print(f"请执行 'source {config_file}' 以应用更改")
