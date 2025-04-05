#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js环境设置主模块，整合其他模块功能。
"""

from ..common import IS_LINUX, IS_MACOS, IS_WINDOWS, PROJECT_ROOT
from .dependencies import check_package_dependencies, install_node_dependencies, verify_markdownlint
from .mcp import check_mcp_servers

# 导入子模块
from .version import (
    check_node,
    check_nvm,
    check_pnpm,
    install_node_with_nvm,
    install_nvm,
    install_pnpm,
)


def setup_node_environment() -> bool:
    """设置Node.js环境，包括nvm安装和依赖配置."""
    print("\n---- Node.js环境设置 ----")

    # 首先尝试检查nvm
    nvm_ok, nvm_version = check_nvm()
    recommended_node_version = "18.12.0"  # 推荐的Node.js版本

    if nvm_ok:
        print(f"发现nvm: {nvm_version}")
        # 提示用户使用nvm安装Node.js
        print(f"建议使用nvm安装Node.js {recommended_node_version}:")
        if IS_WINDOWS:
            print(f"nvm install {recommended_node_version}")
            print(f"nvm use {recommended_node_version}")
        else:
            print(
                f"source ~/.nvm/nvm.sh && nvm install {recommended_node_version} && nvm use {recommended_node_version}"
            )
    else:
        print("未找到nvm，建议安装nvm以管理Node.js版本")
        install_choice = input("是否安装nvm? (y/n): ").lower().strip()
        if install_choice == "y":
            if install_nvm():
                print("请重新运行此脚本以使用nvm安装Node.js")
                return False

    # 检查Node.js
    node_ok, node_version = check_node()
    if not node_ok:
        if nvm_ok:
            install_choice = (
                input(f"是否使用nvm安装Node.js {recommended_node_version}? (y/n): ").lower().strip()
            )
            if install_choice == "y":
                if not install_node_with_nvm(recommended_node_version):
                    return False
            else:
                print("请手动安装Node.js后再运行此脚本")
                return False
        else:
            print("未找到Node.js，请安装Node.js")
            if IS_MACOS:
                print("brew install node")
            elif IS_LINUX:
                print("sudo apt install nodejs npm")
            elif IS_WINDOWS:
                print("请从https://nodejs.org/下载安装Node.js")
            return False
    else:
        print(f"发现 Node.js {node_version}")

    # 检查pnpm
    pnpm_ok, pnpm_version = check_pnpm()
    if not pnpm_ok:
        print("未找到pnpm，正在安装...")
        if not install_pnpm():
            print("请手动安装pnpm: npm install -g pnpm")
            return False
        pnpm_ok, pnpm_version = check_pnpm()
        if not pnpm_ok:
            print("pnpm安装失败")
            return False
    print(f"发现 pnpm {pnpm_version}")

    # 安装Node.js依赖
    if not install_node_dependencies():
        return False

    # 验证markdownlint配置
    if not verify_markdownlint():
        print("markdownlint配置有问题，但将继续安装")

    # 检查MCP服务器
    check_mcp_servers()

    # 检查依赖版本问题
    check_package_dependencies()

    print("Node.js环境设置完成!")
    return True
