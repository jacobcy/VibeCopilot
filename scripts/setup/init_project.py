#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目初始化脚本.

用于基于模板创建新项目，自动生成项目结构和文档。
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# 根据绝对导入规则调整导入顺序
# 如果要导入项目内的模块，应该在文件顶部添加这些导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_operations import ensure_directory, read_file, write_file  # noqa: E402


def get_templates_dir() -> Path:
    """
    获取项目模板目录.

    Returns:
        Path: 模板目录路径
    """
    # 项目根目录
    project_root = Path(__file__).parent.parent.parent
    return project_root / "templates"


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


def init_project(
    project_name: str,
    template_name: str,
    output_dir: Optional[Path] = None,
    variables: Optional[Dict[str, str]] = None,
    ignore_patterns: Optional[Set[str]] = None,
) -> Path:
    """
    初始化一个新项目.

    Args:
        project_name: 项目名称
        template_name: 使用的模板名称
        output_dir: 输出目录，默认为当前目录
        variables: 模板变量
        ignore_patterns: 要忽略的文件/目录模式

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

    ignore_patterns.update(
        {".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.swp"}
    )

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
    return project_dir


def main() -> None:
    """脚本主函数."""
    parser = argparse.ArgumentParser(description="初始化新项目")
    parser.add_argument("--name", "-n", help="项目名称", required=True)
    parser.add_argument("--template", "-t", help="模板名称", required=True)
    parser.add_argument("--output", "-o", help="输出目录", default=None)
    parser.add_argument("--var", "-v", action="append", help="模板变量 (格式: KEY=VALUE)", default=[])
    parser.add_argument("--list", "-l", action="store_true", help="列出可用模板")

    args = parser.parse_args()

    # 列出可用模板
    if args.list:
        templates = list_available_templates()
        if templates:
            print("可用模板:")
            for template in templates:
                print(f"  - {template}")
        else:
            print("没有可用的模板")
        return

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
        )
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
