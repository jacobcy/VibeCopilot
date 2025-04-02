#!/usr/bin/env python3
"""
GitDiagram 项目分析工具

此脚本用于分析项目结构并生成架构图，帮助开发者理解项目框架、
制定路线图或在代码重构后更新项目文档。

使用方法:
  python analyze.py --path /path/to/project [--output /path/to/output] [--instructions "自定义指令"]

参数:
  --path: 要分析的项目路径（必填）
  --output: 输出目录，默认为当前目录
  --instructions: 自定义分析指令，如"突出显示数据流"
  --openai-key: OpenAI API密钥(可选)
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 全局变量
DEFAULT_OUTPUT_DIR = Path.cwd()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # 默认使用环境变量中指定的模型


class GitAnalyzer:
    """Git项目分析器类"""

    def __init__(
        self,
        project_path: str,
        output_path: str = None,
        custom_instructions: str = "",
        openai_key: str = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.output_path = Path(output_path or DEFAULT_OUTPUT_DIR).resolve()
        self.custom_instructions = custom_instructions
        self.openai_key = openai_key or OPENAI_API_KEY

        # 验证项目路径
        if not self.project_path.exists():
            raise ValueError(f"项目路径不存在: {self.project_path}")

        # 确保输出目录存在
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 准备结果文件
        self.diagram_file = self.output_path / "project_diagram.md"
        self.explanation_file = self.output_path / "project_explanation.md"

    def collect_file_paths(self) -> str:
        """收集项目文件路径"""
        print("收集项目文件路径...")

        exclude_patterns = [
            ".git/",
            "node_modules/",
            "venv/",
            "__pycache__/",
            ".vscode/",
            ".idea/",
            "dist/",
            "build/",
            ".DS_Store",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.dll",
            "*.class",
            "*.exe",
            "*.bin",
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.gif",
            "*.ico",
            "*.svg",
            "*.ttf",
            "*.woff",
            "*.webp",
            "yarn.lock",
            "package-lock.json",
            "*.log",
        ]

        def should_include(path: Path) -> bool:
            """判断文件是否应该被包含"""
            path_str = str(path)
            return not any(pattern in path_str for pattern in exclude_patterns)

        paths = []
        for root, dirs, files in os.walk(self.project_path):
            # 修改dirs列表，移除不需要遍历的目录
            dirs[:] = [d for d in dirs if should_include(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file
                if should_include(file_path):
                    # 存储相对路径
                    rel_path = file_path.relative_to(self.project_path)
                    paths.append(str(rel_path))

        return "\n".join(sorted(paths))

    def get_readme_content(self) -> str:
        """获取项目README内容"""
        print("获取项目README内容...")

        readme_candidates = ["README.md", "README", "Readme.md", "readme.md"]

        for candidate in readme_candidates:
            readme_path = self.project_path / candidate
            if readme_path.exists():
                return readme_path.read_text(encoding="utf-8")

        print("警告: 未找到README文件")
        return "项目未包含README文件。"

    def analyze_project(self) -> Tuple[str, str]:
        """分析项目结构并生成架构图"""
        print("开始分析项目结构...")

        # 收集项目数据
        file_tree = self.collect_file_paths()
        readme = self.get_readme_content()

        # 准备请求数据
        data = {"file_tree": file_tree, "readme": readme, "instructions": self.custom_instructions}

        explanation = ""
        component_mapping = ""
        diagram = ""

        try:
            # 模拟GitDiagram的处理流程
            explanation = self._generate_explanation(data)
            component_mapping = self._generate_component_mapping(explanation, data)
            diagram = self._generate_diagram(explanation, component_mapping)
        except Exception as e:
            print(f"错误: 分析过程中出现异常: {e}")
            sys.exit(1)

        return explanation, diagram

    def _generate_explanation(self, data: Dict) -> str:
        """生成项目解释"""
        print("正在生成项目解释...")

        # 使用OpenAI API生成
        if not self.openai_key:
            print("错误: 需要提供OpenAI API密钥")
            sys.exit(1)

        # 构建提示
        system_prompt = """
        您是一位软件架构专家，请分析提供的项目文件结构和README，详细解释该项目的架构和设计。
        您的分析应包括：
        1. 项目的类型和目的
        2. 主要组件和它们的功能
        3. 组件之间的关系和数据流
        4. 使用的技术栈和框架
        5. 架构模式和设计原则
        6. 项目的层次结构

        请提供详细的解释，以便后续可以生成准确的架构图。
        """

        user_prompt = f"""
        请分析以下项目:

        <file_tree>
        {data['file_tree']}
        </file_tree>

        <readme>
        {data['readme']}
        </readme>

        {f"<instructions>{data['instructions']}</instructions>" if data['instructions'] else ""}
        """

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}",
                },
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            explanation = (
                response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            return explanation
        except Exception as e:
            print(f"错误: 调用OpenAI API失败: {e}")
            sys.exit(1)

    def _generate_component_mapping(self, explanation: str, data: Dict) -> str:
        """生成组件映射"""
        print("正在生成组件映射...")

        # 使用OpenAI API生成
        if not self.openai_key:
            print("错误: 需要提供OpenAI API密钥")
            sys.exit(1)

        system_prompt = """
        您是一位软件架构专家，请将系统架构中的组件映射到具体的文件或目录路径。
        分析上下文中的系统解释，找出关键组件，然后将每个组件对应到文件树中的具体路径。

        输出格式必须严格按照：
        <component_mapping>
        1. [组件名称]: [文件/目录路径]
        2. [组件名称]: [文件/目录路径]
        ...
        </component_mapping>
        """

        user_prompt = f"""
        请分析以下系统解释，并将组件映射到对应的文件或目录：

        <explanation>
        {explanation}
        </explanation>

        <file_tree>
        {data['file_tree']}
        </file_tree>
        """

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}",
                },
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            mapping = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

            # 提取<component_mapping>标签中的内容
            match = re.search(r"<component_mapping>(.*?)</component_mapping>", mapping, re.DOTALL)
            if match:
                return match.group(1).strip()
            return mapping
        except Exception as e:
            print(f"错误: 调用OpenAI API失败: {e}")
            sys.exit(1)

    def _generate_diagram(self, explanation: str, component_mapping: str) -> str:
        """生成架构图"""
        print("正在生成架构图...")

        # 使用OpenAI API生成
        if not self.openai_key:
            print("错误: 需要提供OpenAI API密钥")
            sys.exit(1)

        system_prompt = """
        您是一位软件架构专家，请根据系统解释和组件映射生成Mermaid格式的架构图。

        遵循以下规则：
        1. 使用flowchart TD生成自上而下的流程图
        2. 为不同类型的组件使用适当的形状和样式
        3. 确保节点之间的关系清晰
        4. 使用子图(subgraph)对相关组件进行分组
        5. 添加颜色样式增强可读性
        6. 为映射的组件添加点击事件，格式为: click ComponentName "path/to/file"
        7. 图表应垂直排列，避免过长的水平列表

        输出必须是有效的Mermaid.js代码，不要加任何额外说明。
        """

        user_prompt = f"""
        请基于以下信息生成架构图：

        <explanation>
        {explanation}
        </explanation>

        <component_mapping>
        {component_mapping}
        </component_mapping>
        """

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_key}",
                },
                json={
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            diagram = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

            # 清理输出，移除可能的```mermaid和```标记
            diagram = re.sub(r"^```mermaid\s*\n", "", diagram)
            diagram = re.sub(r"\n```$", "", diagram)

            return diagram
        except Exception as e:
            print(f"错误: 调用OpenAI API失败: {e}")
            sys.exit(1)

    def save_results(self, explanation: str, diagram: str) -> None:
        """保存分析结果"""
        print("正在保存分析结果...")

        # 保存解释文件
        with open(self.explanation_file, "w", encoding="utf-8") as f:
            f.write("# 项目架构解释\n\n")
            f.write(explanation)

        # 保存图表文件
        with open(self.diagram_file, "w", encoding="utf-8") as f:
            f.write("# 项目架构图\n\n")
            f.write("```mermaid\n")
            f.write(diagram)
            f.write("\n```\n")

        print(f"✅ 解释文件已保存至: {self.explanation_file}")
        print(f"✅ 架构图已保存至: {self.diagram_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GitDiagram项目分析工具")
    parser.add_argument("--path", required=True, help="要分析的项目路径")
    parser.add_argument("--output", help="输出目录，默认为当前目录")
    parser.add_argument("--instructions", help="自定义分析指令，例如'突出显示数据流'")
    parser.add_argument("--openai-key", help="OpenAI API密钥")

    args = parser.parse_args()

    try:
        analyzer = GitAnalyzer(
            project_path=args.path,
            output_path=args.output,
            custom_instructions=args.instructions or "",
            openai_key=args.openai_key,
        )

        explanation, diagram = analyzer.analyze_project()
        analyzer.save_results(explanation, diagram)

        print("\n🎉 项目分析完成！")
        print("您可以在输出目录中查看解释文件和架构图。")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
