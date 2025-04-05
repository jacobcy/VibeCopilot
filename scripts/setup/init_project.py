#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot环境配置脚本 - 重构版。

该脚本专注于:
1. 设置Python开发环境，包括虚拟环境创建
2. 安装项目依赖
3. 注册命令行工具
4. 配置Node.js开发环境和工具

优化点:
1. 模块化设计，拆分功能到不同模块
2. 跨平台支持 (Windows, macOS, Linux)
3. 支持nvm管理Node.js版本
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.append(str(Path(__file__).parent))

# 导入功能模块
from modules.common import IS_WINDOWS, PROJECT_ROOT
from modules.node_setup import setup_node_environment
from modules.python_setup import setup_precommit, setup_python_environment


def setup_environment() -> bool:
    """设置项目环境。"""
    print("=" * 80)
    print("正在设置VibeCopilot开发环境...")
    print("=" * 80)

    # 步骤1: 设置Python环境
    print("\n---- Python环境设置 ----")
    if not setup_python_environment():
        print("Python环境设置失败")
        return False

    # 步骤2: 设置Node.js环境
    print("\n---- Node.js环境设置 ----")
    if not setup_node_environment():
        print("Node.js环境设置失败")
        return False

    # 步骤3: 安装pre-commit钩子
    print("\n---- pre-commit钩子设置 ----")
    venv_path = PROJECT_ROOT / ".venv"
    if not setup_precommit(venv_path):
        print("pre-commit钩子设置失败，但将继续安装流程")

    # 步骤4: 检查配置文件
    print("\n---- 配置文件检查 ----")
    config_dir = PROJECT_ROOT / "config" / "default"
    if not config_dir.exists():
        print(f"警告: 未找到配置目录: {config_dir}")

    print("\n" + "=" * 80)
    print("✅ 环境设置完成！")
    print("=" * 80)

    # 终端命令
    if IS_WINDOWS:
        print(f"\n使用 '{venv_path}\\Scripts\\activate' 激活环境")
    else:
        print(f"\n使用 'source {venv_path}/bin/activate' 激活环境")
    print("使用 'deactivate' 退出环境")
    print("\n现在可以使用 'vibecopilot' 命令了")
    return True


def main() -> None:
    """脚本主函数。"""
    if not setup_environment():
        sys.exit(1)


if __name__ == "__main__":
    main()
