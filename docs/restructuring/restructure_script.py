#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Roadmap模块重构助手脚本

此脚本帮助执行重构过程中的文件迁移、创建目录和备份操作
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def create_backup(path: str) -> str:
    """创建文件或目录的备份

    Args:
        path: 要备份的文件或目录路径

    Returns:
        备份文件路径
    """
    backup_path = f"{path}.bak"
    if os.path.exists(path):
        if os.path.isdir(path):
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(path, backup_path)
        else:
            shutil.copy2(path, backup_path)
        print(f"已创建备份: {backup_path}")
    return backup_path


def ensure_directory(path: str) -> None:
    """确保目录存在

    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)
    print(f"确保目录存在: {path}")


def move_file(source: str, destination: str) -> None:
    """移动文件，并确保目标目录存在

    Args:
        source: 源文件路径
        destination: 目标文件路径
    """
    dest_dir = os.path.dirname(destination)
    ensure_directory(dest_dir)
    if os.path.exists(source):
        shutil.move(source, destination)
        print(f"已移动文件: {source} -> {destination}")
    else:
        print(f"源文件不存在，无法移动: {source}")


def create_file(path: str, content: str) -> None:
    """创建文件，写入内容

    Args:
        path: 文件路径
        content: 文件内容
    """
    dest_dir = os.path.dirname(path)
    ensure_directory(dest_dir)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已创建文件: {path}")


def create_compatibility_layer() -> None:
    """创建兼容性层"""
    content = '''"""
兼容性导入，重定向到新的模块位置
"""
import warnings

warnings.warn(
    "adapters.projects 模块已被弃用，请使用 adapters.github_project 或 adapters.roadmap_sync",
    DeprecationWarning,
    stacklevel=2
)

# 导入重定向
from adapters.github_project.roadmap.generator import RoadmapGenerator
from adapters.github_project.roadmap.processor import RoadmapProcessor
from adapters.github_project.roadmap.importer import ImportRoadmap as RoadmapImporter
from adapters.roadmap_sync.connector import RoadmapConnector as ProjectConnector

__all__ = [
    "RoadmapGenerator",
    "RoadmapProcessor",
    "RoadmapImporter",
    "ProjectConnector"
]
'''
    # 创建兼容性导入文件
    create_file(os.path.join(PROJECT_ROOT, "adapters/projects/__init__.py"), content)
    print("已创建兼容性层")


def update_readme(module: str) -> None:
    """更新README文件

    Args:
        module: 模块名称("roadmap_sync"或"github_project")
    """
    if module == "roadmap_sync":
        content = """# 轻量级Markdown路线图工具

这是一个轻量级的Markdown路线图工具，专注于YAML和Markdown格式的双向转换。

## 核心功能

- **Markdown为中心**：使用Markdown文件作为数据源
- **双向转换**: 支持roadmap.yaml和Markdown故事文件之间的转换
- **命令行接口**：简单的CLI命令用于管理路线图文件
- **最小实现**：专注于文件格式转换

## 主要组件

- **markdown_parser.py**: 从Markdown读取故事数据
- **models.py**: 简单的数据模型
- **cli.py**: 命令行接口
- **converter/**: 提供YAML和Markdown之间的转换功能
  - **yaml_to_markdown.py**: 将roadmap.yaml转换为标准化的stories目录结构
  - **markdown_to_yaml.py**: 将stories目录转换为roadmap.yaml
  - **cli.py**: 转换器命令行工具

## 实现说明

本模块专注于文件格式转换，若需GitHub集成功能，请使用`adapters/github_project`模块。
"""
        create_file(os.path.join(PROJECT_ROOT, "adapters/roadmap_sync/README.md"), content)

    elif module == "github_project":
        content = """# GitHub Project 系统

## 简介

这是一个完整的GitHub Projects V2集成系统，提供高级项目管理、分析和路线图同步功能。支持与GitHub Projects的深度集成，包括自定义字段、看板视图和自动化流程。

## 核心功能

- **项目分析**: 自动分析项目进度、质量和风险
- **时间线调整**: 根据实际进度自动调整项目时间线
- **报告生成**: 生成项目状态报告和调整建议
- **路线图同步**: 与GitHub项目的双向同步
- **交互式管理**: 提供命令行和交互式界面管理项目

## 组件说明

- `api/`: GitHub API客户端实现
  - `github_client.py`: 基础API客户端
  - `projects_client.py`: Projects V2专用API客户端
  - `issues_client.py`: Issues API客户端

- `roadmap/`: 路线图管理功能
  - `roadmap_generator.py`: 生成和更新项目路线图
  - `roadmap_processor.py`: 处理路线图数据
  - `import_roadmap.py`: 导入外部路线图数据

- `analysis/`: 项目分析功能

- `manage_project.py`: 交互式项目管理工具
- `cli.py`: 项目分析命令行工具
- `weekly_update.sh`: 项目周报自动分析脚本

## 使用场景

- 适合复杂项目管理
- 需要高级数据分析和可视化
- 使用GitHub Projects V2作为主要项目管理工具
- 需要自动调整和项目预测
"""
        create_file(os.path.join(PROJECT_ROOT, "adapters/github_project/README.md"), content)


def restructure_roadmap_modules() -> None:
    """执行GitHub Roadmap模块重构过程"""
    # 备份原始文件
    print("开始备份原始文件...")
    create_backup(os.path.join(PROJECT_ROOT, "adapters/roadmap_sync"))
    create_backup(os.path.join(PROJECT_ROOT, "adapters/github_project"))
    create_backup(os.path.join(PROJECT_ROOT, "adapters/projects"))
    create_backup(os.path.join(PROJECT_ROOT, "src/roadmap"))

    # 创建新的目录结构
    print("\n创建新的目录结构...")
    ensure_directory(os.path.join(PROJECT_ROOT, "adapters/github_project/roadmap"))

    # 移动文件
    print("\n移动文件...")
    files_to_move = [
        # (源文件, 目标文件)
        (
            os.path.join(PROJECT_ROOT, "adapters/projects/roadmap_generator.py"),
            os.path.join(PROJECT_ROOT, "adapters/github_project/roadmap/generator.py"),
        ),
        (
            os.path.join(PROJECT_ROOT, "adapters/projects/roadmap_processor.py"),
            os.path.join(PROJECT_ROOT, "adapters/github_project/roadmap/processor.py"),
        ),
        (
            os.path.join(PROJECT_ROOT, "adapters/projects/import_roadmap.py"),
            os.path.join(PROJECT_ROOT, "adapters/github_project/roadmap/importer.py"),
        ),
    ]

    for source, destination in files_to_move:
        move_file(source, destination)

    # 创建兼容性层
    print("\n创建兼容性层...")
    create_compatibility_layer()

    # 更新README
    print("\n更新README...")
    update_readme("roadmap_sync")
    update_readme("github_project")

    # 创建roadmap模块的__init__.py
    print("\n创建初始化文件...")
    create_file(
        os.path.join(PROJECT_ROOT, "adapters/github_project/roadmap/__init__.py"),
        '"""GitHub路线图管理模块"""\n\n__all__ = ["generator", "processor", "importer"]\n',
    )

    print("\n重构完成!")
    print("请查看重构报告获取下一步操作指南。")


def generate_report() -> None:
    """生成重构报告"""
    report = """# GitHub Roadmap模块重构报告

## 重构操作已完成
- 创建了新的目录结构
- 移动了关键文件
- 创建了兼容性层
- 更新了README文件

## 下一步操作
1. 检查移动的文件，确保导入路径正确
2. 更新src/roadmap模块以使用新的组件
3. 运行测试确保功能正常
4. 删除不再需要的文件

## 注意事项
- 所有原始文件都已备份(*.bak)
- 建议先保留备份，直到确认所有功能正常
"""
    report_path = os.path.join(PROJECT_ROOT, "docs/restructuring/restructure_report.md")
    create_file(report_path, report)
    print(f"报告已生成: {report_path}")


if __name__ == "__main__":
    print("GitHub Roadmap模块重构助手")
    print("=" * 30)
    print(f"项目根目录: {PROJECT_ROOT}")
    print("=" * 30)

    choice = input("开始重构过程? [y/N]: ").strip().lower()
    if choice == "y":
        restructure_roadmap_modules()
        generate_report()
    else:
        print("重构已取消")
