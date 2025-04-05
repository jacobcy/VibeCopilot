#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python环境配置模块。
"""

from pathlib import Path

from .common import IS_LINUX, IS_MACOS, IS_WINDOWS, PROJECT_ROOT, get_python_path, run_command


def check_python() -> tuple[bool, str]:
    """检查Python环境."""
    try:
        cmd = ["python", "--version"] if IS_WINDOWS else ["python3", "--version"]
        returncode, output = run_command(cmd)
        if returncode == 0:
            return True, output.strip()
        return False, "无法获取Python版本"
    except Exception as e:
        return False, f"检查Python出错: {e}"


def check_uv() -> tuple[bool, str]:
    """检查uv是否已安装."""
    try:
        cmd = ["where", "uv"] if IS_WINDOWS else ["which", "uv"]
        returncode, output = run_command(cmd)
        if returncode == 0:
            retcode, vers = run_command(["uv", "--version"])
            if retcode == 0:
                return True, vers.strip()
            return True, "已安装，但无法获取版本"
        return False, "未找到uv"
    except Exception:
        return False, "uv未安装"


def install_uv() -> bool:
    """安装uv工具."""
    print("正在安装uv...")

    if IS_MACOS or IS_LINUX:
        cmd = ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "/tmp/uv_install.sh"]
        returncode, _ = run_command(cmd)
        if returncode != 0:
            print("下载uv安装脚本失败")
            return False

        import os

        install_script = "/tmp/uv_install.sh"
        os.chmod(install_script, 0o755)
        returncode, output = run_command([install_script])
        if returncode != 0:
            print(f"安装uv失败: {output}")
            return False

        print("uv安装成功")
        return True
    elif IS_WINDOWS:
        print("Windows系统请参考以下链接手动安装uv: https://github.com/astral-sh/uv/releases")
        return False
    else:
        print("不支持的操作系统，请手动安装uv: https://github.com/astral-sh/uv")
        return False


def setup_python_environment() -> bool:
    """设置Python环境，包括虚拟环境创建和依赖安装."""
    # 检查Python
    python_ok, python_version = check_python()
    if not python_ok:
        if IS_MACOS:
            print("未找到Python 3，请安装Python 3.13")
            print("brew install python@3.13")
        elif IS_LINUX:
            print("未找到Python 3，请安装Python 3.10+")
            print("sudo apt update && sudo apt install python3 python3-pip python3-venv")
        elif IS_WINDOWS:
            print("未找到Python，请从https://www.python.org/downloads/windows/下载安装")
        return False
    print(f"发现 {python_version}")

    # 检查uv
    uv_ok, uv_version = check_uv()
    if not uv_ok:
        if not install_uv():
            return False
    else:
        print(f"已安装uv: {uv_version}")

    # 创建虚拟环境
    venv_path = PROJECT_ROOT / ".venv"
    if not venv_path.exists():
        print("创建虚拟环境...")
        python_path = get_python_path()
        returncode, output = run_command(
            ["uv", "venv", f"--python={python_path}", ".venv"], cwd=PROJECT_ROOT
        )
        if returncode != 0:
            print(f"创建虚拟环境失败: {output}")
            return False

    # 安装Python依赖和注册命令
    print("安装Python项目依赖...")
    returncode, output = run_command(
        ["uv", "pip", "install", "-e", ".[dev,docs]"], cwd=PROJECT_ROOT
    )
    if returncode != 0:
        print(f"安装Python依赖失败: {output}")
        return False

    print("Python环境设置完成!")
    return True


def setup_precommit(venv_path: Path) -> bool:
    """安装pre-commit钩子."""
    print("安装pre-commit钩子...")

    precommit_exec = "pre-commit.exe" if IS_WINDOWS else "pre-commit"
    precommit_script = venv_path / ("Scripts" if IS_WINDOWS else "bin") / precommit_exec

    if Path(precommit_script).exists():
        returncode, output = run_command([str(precommit_script), "install"], cwd=PROJECT_ROOT)
        if returncode != 0:
            print(f"安装pre-commit钩子失败: {output}")
            return False
        print("pre-commit钩子安装成功")
        return True

    print(f"未找到pre-commit: {precommit_script}")
    return False
