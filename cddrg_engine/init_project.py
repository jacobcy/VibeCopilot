#!/usr/bin/env python
"""CDDRG引擎项目初始化脚本."""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """检查Python版本."""
    min_version = (3, 11)
    current = sys.version_info[:2]

    if current < min_version:
        print(f"错误: 需要Python {min_version[0]}.{min_version[1]}或更高版本")
        print(f"当前版本: {current[0]}.{current[1]}")
        sys.exit(1)

    print(f"Python版本检查通过: {current[0]}.{current[1]}")


def check_uv_installed():
    """检查uv是否已安装."""
    try:
        subprocess.run(
            ["uv", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        print("已安装uv")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("未找到uv")
        return False


def install_uv():
    """安装uv工具."""
    system = platform.system().lower()

    if system == "darwin":  # macOS
        try:
            subprocess.run(["brew", "install", "astral-sh/tap/uv"], check=True)
            print("通过Homebrew安装uv成功")
            return True
        except subprocess.CalledProcessError:
            print("通过Homebrew安装uv失败")
    elif system == "linux":
        try:
            subprocess.run(
                ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"],
                shell=True,
                check=True,
            )
            print("通过安装脚本安装uv成功")
            return True
        except subprocess.CalledProcessError:
            print("通过安装脚本安装uv失败")

    print("请手动安装uv: https://github.com/astral-sh/uv")
    return False


def setup_virtual_env(dev_mode=False):
    """设置虚拟环境."""
    venv_path = Path(".venv")

    if venv_path.exists():
        print(f"虚拟环境已存在: {venv_path}")
    else:
        print("创建虚拟环境...")
        subprocess.run(["python", "-m", "venv", ".venv"], check=True)
        print(f"虚拟环境创建成功: {venv_path}")

    # 确定激活脚本路径
    if platform.system().lower() == "windows":
        activate_script = venv_path / "Scripts" / "activate"
    else:
        activate_script = venv_path / "bin" / "activate"

    print(f"激活虚拟环境: {activate_script}")

    # 安装依赖
    if dev_mode:
        install_cmd = ["uv", "pip", "install", "-e", ".[dev]"]
    else:
        install_cmd = ["uv", "pip", "install", "-e", "."]

    print(f"安装项目依赖: {' '.join(install_cmd)}")
    subprocess.run(install_cmd, check=True)

    print("项目依赖安装完成")

    # 返回激活命令提示
    if platform.system().lower() == "windows":
        return f".venv\\Scripts\\activate"
    else:
        return f"source .venv/bin/activate"


def update_git_status():
    """更新Git状态."""
    try:
        # 检查是否在Git仓库中
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print("未在Git仓库中，跳过Git操作")
            return

        # 添加所有文件
        subprocess.run(["git", "add", "."], check=True)
        print("已将所有文件添加到Git暂存区")

        # 检查状态
        status = subprocess.run(["git", "status"], stdout=subprocess.PIPE, text=True, check=True)
        print("Git状态:")
        print(status.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Git操作失败: {e}")


def main():
    """主函数."""
    parser = argparse.ArgumentParser(description="CDDRG引擎项目初始化工具")
    parser.add_argument("--dev", action="store_true", help="安装开发依赖")
    parser.add_argument("--skip-git", action="store_true", help="跳过Git操作")

    args = parser.parse_args()

    print("===== CDDRG引擎项目初始化 =====")

    # 确保在项目根目录
    if not os.path.exists("pyproject.toml"):
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)

    check_python_version()

    if not check_uv_installed():
        if not install_uv():
            print("请先安装uv工具后再运行此脚本")
            sys.exit(1)

    activate_cmd = setup_virtual_env(dev_mode=args.dev)

    if not args.skip_git:
        update_git_status()

    print("\n===== 初始化完成! =====")
    print(f"激活虚拟环境: {activate_cmd}")
    print("安装完成后，可以运行测试: pytest")
    print("或导入引擎: from cddrg_engine import Engine")


if __name__ == "__main__":
    main()
