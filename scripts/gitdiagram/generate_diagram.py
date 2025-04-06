#!/usr/bin/env python
"""
生成项目结构图的工具脚本，调用gitdiagram子模块的功能
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
GITDIAGRAM_DIR = ROOT_DIR / "modules" / "gitdiagram"


def setup_gitdiagram():
    """设置gitdiagram环境"""
    if not (GITDIAGRAM_DIR / "node_modules").exists():
        print("正在安装gitdiagram依赖...")
        subprocess.run(["pnpm", "install"], cwd=GITDIAGRAM_DIR, check=True)

    if not (GITDIAGRAM_DIR / ".env").exists():
        print("创建gitdiagram环境配置...")
        subprocess.run(["cp", ".env.example", ".env"], cwd=GITDIAGRAM_DIR, check=True)


def start_backend():
    """启动gitdiagram后端服务"""
    print("启动gitdiagram后端...")
    subprocess.run(["docker-compose", "up", "-d"], cwd=GITDIAGRAM_DIR, check=True)
    print("gitdiagram后端服务已启动")


def generate_diagram(repo_url, output_file=None):
    """
    生成项目结构图

    Args:
        repo_url: GitHub仓库URL
        output_file: 输出文件路径
    """
    if not repo_url.startswith(("http://", "https://")):
        # 假设是本地路径，转换为file URL
        repo_path = Path(repo_url).absolute()
        if not repo_path.exists():
            print(f"错误: 路径 {repo_path} 不存在")
            return
        repo_url = f"file://{repo_path}"

    # 这里模拟调用gitdiagram的功能
    # 实际实现需要根据gitdiagram的API进行调整
    print(f"生成 {repo_url} 的项目结构图...")

    if output_file:
        output_path = Path(output_file)
        print(f"图表将保存到: {output_path}")

    print("提示: 由于gitdiagram是一个网页应用，实际使用时请运行前端服务并访问对应URL")
    print("前端服务启动命令: cd modules/gitdiagram && pnpm dev")


def main():
    parser = argparse.ArgumentParser(description="生成项目结构图")
    parser.add_argument("repo", help="GitHub仓库URL或本地路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--setup", action="store_true", help="设置gitdiagram环境")
    parser.add_argument("--start-backend", action="store_true", help="启动gitdiagram后端服务")

    args = parser.parse_args()

    if args.setup:
        setup_gitdiagram()

    if args.start_backend:
        start_backend()

    generate_diagram(args.repo, args.output)


if __name__ == "__main__":
    main()
