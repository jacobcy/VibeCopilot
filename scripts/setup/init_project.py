#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目初始化与环境设置脚本.

该脚本有两个主要功能:
1. 基于模板创建新项目，自动生成项目结构和文档
2. 设置Python开发环境，包括虚拟环境创建和依赖安装
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 根据绝对导入规则调整导入顺序
# 如果要导入项目内的模块，应该在文件顶部添加这些导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_operations import ensure_directory, read_file, write_file  # noqa: E402

# 路径常量
PYTHON_PATH = "/opt/homebrew/opt/python@3.13/bin/python3"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_templates_dir() -> Path:
    """
    获取项目模板目录.

    Returns:
        Path: 模板目录路径
    """
    return PROJECT_ROOT / "templates"


def list_available_templates() -> List[str]:
    """
    列出可用的项目模板.

    Returns:
        List[str]: 可用模板名称列表
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return []

    return [d.name for d in templates_dir.iterdir() if d.is_dir()]


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    """
    执行Shell命令并返回结果.

    Args:
        cmd: 命令和参数列表
        cwd: 执行命令的工作目录

    Returns:
        Tuple[int, str]: 退出码和命令输出
    """
    process = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    return process.returncode, process.stdout


def check_python() -> Tuple[bool, str]:
    """
    检查Python环境.

    Returns:
        Tuple[bool, str]: 检查结果和Python版本
    """
    try:
        returncode, output = run_command(["python3", "--version"])
        if returncode == 0:
            return True, output.strip()
        return False, "无法获取Python版本"
    except Exception as e:
        return False, f"检查Python出错: {e}"


def check_uv() -> Tuple[bool, str]:
    """
    检查uv是否已安装.

    Returns:
        Tuple[bool, str]: 检查结果和uv版本
    """
    try:
        returncode, output = run_command(["which", "uv"])
        if returncode == 0:
            retcode, vers = run_command(["uv", "--version"])
            if retcode == 0:
                return True, vers.strip()
            return True, "已安装，但无法获取版本"
        return False, "未找到uv"
    except Exception:
        return False, "uv未安装"


def install_uv() -> bool:
    """
    安装uv工具.

    Returns:
        bool: 安装是否成功
    """
    print("正在安装uv...")
    if platform.system() == "Darwin" or platform.system() == "Linux":
        cmd = ["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "/tmp/uv_install.sh"]
        returncode, _ = run_command(cmd)
        if returncode != 0:
            print("下载uv安装脚本失败")
            return False

        # 执行安装脚本
        os.chmod("/tmp/uv_install.sh", 0o755)
        returncode, output = run_command(["/tmp/uv_install.sh"])
        if returncode != 0:
            print(f"安装uv失败: {output}")
            return False

        print("uv安装成功")
        return True
    else:
        print("不支持的操作系统，请手动安装uv: https://github.com/astral-sh/uv")
        return False


def setup_venv(project_dir: Path) -> bool:
    """
    设置项目虚拟环境.

    Args:
        project_dir: 项目目录

    Returns:
        bool: 设置是否成功
    """
    print(f"正在为 {project_dir.name} 设置Python环境...")

    # 检查Python
    python_ok, python_version = check_python()
    if not python_ok:
        print("未找到Python 3，请安装Python 3.13")
        print("brew install python@3.13")
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
    venv_path = project_dir / ".venv"
    if not venv_path.exists():
        print("创建虚拟环境...")
        returncode, output = run_command(
            ["uv", "venv", f"--python={PYTHON_PATH}", ".venv"], cwd=project_dir
        )
        if returncode != 0:
            print(f"创建虚拟环境失败: {output}")
            return False

    # 安装依赖
    print("安装项目依赖...")
    venv_python = str(venv_path / "bin" / "python")
    returncode, output = run_command(["uv", "pip", "install", "-e", ".[dev,docs]"], cwd=project_dir)
    if returncode != 0:
        print(f"安装依赖失败: {output}")
        return False

    # 安装pre-commit钩子
    print("安装pre-commit钩子...")
    precommit_script = str(venv_path / "bin" / "pre-commit")
    if Path(precommit_script).exists():
        returncode, output = run_command([precommit_script, "install"], cwd=project_dir)
        if returncode != 0:
            print(f"安装pre-commit钩子失败: {output}")
            return False

    print("✅ 环境设置完成！")
    print(f"使用 'source {venv_path}/bin/activate' 激活环境")
    print("使用 'deactivate' 退出环境")
    return True


def init_project(
    project_name: str,
    template_name: str,
    output_dir: Optional[Path] = None,
    variables: Optional[Dict[str, str]] = None,
    ignore_patterns: Optional[Set[str]] = None,
    setup_environment: bool = False,
) -> Path:
    """
    初始化一个新项目.

    Args:
        project_name: 项目名称
        template_name: 使用的模板名称
        output_dir: 输出目录，默认为当前目录
        variables: 模板变量
        ignore_patterns: 要忽略的文件/目录模式
        setup_environment: 是否设置Python环境

    Returns:
        Path: 新项目的目录路径

    Raises:
        ValueError: 如果模板不存在
    """
    # 获取模板目录
    templates_dir = get_templates_dir()
    template_dir = templates_dir / template_name

    if not template_dir.exists() or not template_dir.is_dir():
        available = ", ".join(list_available_templates())
        raise ValueError(f"模板 '{template_name}' 不存在。可用模板: {available}")

    # 确定输出目录
    if output_dir is None:
        output_dir = Path.cwd()

    # 创建项目目录
    project_dir = output_dir / project_name
    ensure_directory(project_dir)

    # 默认变量
    if variables is None:
        variables = {}

    variables.update(
        {
            "PROJECT_NAME": project_name,
            "PROJECT_NAME_LOWERCASE": project_name.lower(),
            "PROJECT_NAME_SNAKE_CASE": project_name.lower().replace("-", "_").replace(" ", "_"),
        }
    )

    # 默认忽略模式
    if ignore_patterns is None:
        ignore_patterns = set()

    ignore_patterns.update({".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.swp"})

    # 复制模板文件
    for src_path in template_dir.glob("**/*"):
        # 忽略特定文件/目录
        if any(
            Path(src_path.relative_to(template_dir)).match(pattern) for pattern in ignore_patterns
        ):
            continue

        # 计算目标路径
        rel_path = src_path.relative_to(template_dir)
        dst_path = project_dir / rel_path

        if src_path.is_dir():
            # 创建目录
            ensure_directory(dst_path)
        else:
            # 读取和处理文件内容
            try:
                content = read_file(src_path)

                # 替换变量
                for var_name, var_value in variables.items():
                    content = content.replace(f"{{{{ {var_name} }}}}", var_value)

                # 写入处理后的内容
                write_file(dst_path, content)

            except UnicodeDecodeError:
                # 如果是二进制文件，直接复制
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.write_bytes(src_path.read_bytes())

    print(f"项目 '{project_name}' 已在 {project_dir} 创建完成")

    # 设置Python环境
    if setup_environment:
        setup_venv(project_dir)

    return project_dir


def setup_env() -> None:
    """设置当前项目环境."""
    python_ok, python_version = check_python()
    if not python_ok:
        print("未找到Python 3，请安装Python 3.13")
        print("brew install python@3.13")
        sys.exit(1)
    print(f"发现 {python_version}")

    setup_venv(PROJECT_ROOT)


def main() -> None:
    """脚本主函数."""
    parser = argparse.ArgumentParser(description="项目初始化与环境设置")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 初始化项目子命令
    init_parser = subparsers.add_parser("init", help="初始化新项目")
    init_parser.add_argument("--name", "-n", help="项目名称", required=True)
    init_parser.add_argument("--template", "-t", help="模板名称", required=True)
    init_parser.add_argument("--output", "-o", help="输出目录", default=None)
    init_parser.add_argument(
        "--var", "-v", action="append", help="模板变量 (格式: KEY=VALUE)", default=[]
    )
    init_parser.add_argument("--setup-env", "-s", action="store_true", help="设置Python环境")

    # 设置环境子命令
    setup_parser = subparsers.add_parser("setup", help="设置Python环境")

    # 列出模板子命令
    list_parser = subparsers.add_parser("list", help="列出可用模板")

    args = parser.parse_args()

    # 处理不同命令
    if args.command == "list" or getattr(args, "list", False):
        templates = list_available_templates()
        if templates:
            print("可用模板:")
            for template in templates:
                print(f"  - {template}")
        else:
            print("没有可用的模板")
        return

    elif args.command == "setup":
        setup_env()
        return

    elif args.command == "init":
        # 解析变量
        variables = {}
        for var in args.var:
            if "=" in var:
                key, value = var.split("=", 1)
                variables[key] = value

        # 初始化项目
        output_dir = Path(args.output) if args.output else None

        try:
            init_project(
                project_name=args.name,
                template_name=args.template,
                output_dir=output_dir,
                variables=variables,
                setup_environment=args.setup_env,
            )
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # 默认显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()
