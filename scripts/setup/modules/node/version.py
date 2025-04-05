#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js版本管理模块，包括nvm支持和基本检查功能。
"""

import os
from pathlib import Path

from ..common import IS_LINUX, IS_MACOS, IS_WINDOWS, PROJECT_ROOT, run_command


def check_nvm() -> tuple[bool, str]:
    """检查nvm是否已安装."""
    if IS_WINDOWS:
        # Windows下通常nvm-windows是独立程序
        nvm_path = (
            Path(os.environ.get("NVM_HOME", "C:\\Users\\%USERNAME%\\AppData\\Roaming\\nvm"))
            / "nvm.exe"
        )
        if nvm_path.exists():
            returncode, output = run_command(["nvm", "version"])
            if returncode == 0:
                return True, output.strip()
    else:
        # Linux/macOS下nvm通常是shell函数
        nvm_path = Path.home() / ".nvm" / "nvm.sh"
        if nvm_path.exists():
            return True, "已安装(shell函数)"

    return False, "nvm未安装"


def install_nvm() -> bool:
    """安装nvm."""
    print("正在安装nvm...")
    if IS_MACOS or IS_LINUX:
        cmd = [
            "bash",
            "-c",
            "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash",
        ]
        returncode, output = run_command(cmd)
        if returncode != 0:
            print(f"安装nvm失败: {output}")
            return False

        print("nvm安装成功，请重新启动终端或运行以下命令加载nvm:")
        print("source ~/.nvm/nvm.sh")
        return True
    elif IS_WINDOWS:
        print("Windows系统请从以下地址下载nvm-windows安装程序:")
        print("https://github.com/coreybutler/nvm-windows/releases")
        return False

    return False


def install_node_with_nvm(version: str = "18.12.0") -> bool:
    """使用nvm安装指定版本的Node.js."""
    print(f"使用nvm安装Node.js {version}...")

    if IS_WINDOWS:
        returncode, output = run_command(["nvm", "install", version])
        if returncode != 0:
            print(f"使用nvm安装Node.js失败: {output}")
            return False

        returncode, output = run_command(["nvm", "use", version])
        if returncode != 0:
            print(f"切换到Node.js {version}失败: {output}")
            return False
    else:
        # Linux/macOS下nvm是shell函数，需要特殊处理
        print("请在终端手动执行以下命令安装Node.js:")
        print(f"source ~/.nvm/nvm.sh && nvm install {version} && nvm use {version}")
        return False

    print(f"Node.js {version}安装并激活成功")
    return True


def check_node() -> tuple[bool, str]:
    """检查Node.js环境."""
    try:
        returncode, output = run_command(["node", "--version"])
        if returncode == 0:
            return True, output.strip()
        return False, "无法获取Node.js版本"
    except Exception:
        return False, "Node.js未安装"


def check_npm() -> tuple[bool, str]:
    """检查npm是否已安装."""
    try:
        returncode, output = run_command(["npm", "--version"])
        if returncode == 0:
            return True, output.strip()
        return False, "无法获取npm版本"
    except Exception:
        return False, "npm未安装"


def check_pnpm() -> tuple[bool, str]:
    """检查pnpm是否已安装."""
    try:
        returncode, output = run_command(["pnpm", "--version"])
        if returncode == 0:
            return True, output.strip()
        return False, "无法获取pnpm版本"
    except Exception:
        return False, "pnpm未安装"


def install_pnpm() -> bool:
    """安装pnpm包管理器."""
    print("正在安装pnpm...")
    returncode, output = run_command(["npm", "install", "-g", "pnpm"])
    if returncode != 0:
        print(f"安装pnpm失败: {output}")
        return False
    print("pnpm安装成功")
    return True
