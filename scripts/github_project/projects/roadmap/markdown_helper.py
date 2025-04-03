"""
Markdown解析和生成辅助模块

提供对Markdown文件的解析和生成功能，支持路线图数据的导入和导出。
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml


def parse_markdown_file(file_path: str) -> Dict[str, Any]:
    """
    解析包含路线图数据的Markdown文件

    Args:
        file_path: Markdown文件路径

    Returns:
        Dict[str, Any]: 解析后的路线图数据
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析frontmatter和Markdown内容
    frontmatter, markdown_content = _extract_frontmatter(content)

    # 合并frontmatter和解析的Markdown内容
    result = frontmatter.copy()

    # 解析Markdown内容中的额外数据
    parsed_data = _parse_markdown_content(markdown_content)

    # 合并解析的数据
    for key, value in parsed_data.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], list) and isinstance(value, list):
            # 合并列表
            result[key].extend(value)

    return result


def generate_markdown(roadmap_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    从路线图数据生成Markdown

    Args:
        roadmap_data: 路线图数据
        output_path: 可选的输出文件路径

    Returns:
        str: 生成的Markdown内容
    """
    # 提取frontmatter数据
    frontmatter_data = {}
    non_frontmatter_keys = ["milestones", "tasks", "content"]

    for key, value in roadmap_data.items():
        if key not in non_frontmatter_keys:
            frontmatter_data[key] = value

    # 生成frontmatter
    frontmatter_yaml = yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)
    markdown = f"---\n{frontmatter_yaml}---\n\n"

    # 添加标题
    if "title" in roadmap_data:
        markdown += f"# {roadmap_data['title']}\n\n"

    # 添加描述
    if "description" in roadmap_data:
        markdown += f"{roadmap_data['description']}\n\n"

    # 添加里程碑
    if "milestones" in roadmap_data and roadmap_data["milestones"]:
        markdown += "## 里程碑\n\n"

        for milestone in roadmap_data["milestones"]:
            name = milestone.get("name", "")
            description = milestone.get("description", "")
            progress = milestone.get("progress", 0)
            start_date = milestone.get("start_date", "")
            end_date = milestone.get("end_date", "")

            markdown += f"### {name}\n\n"

            if description:
                markdown += f"{description}\n\n"

            markdown += f"- 进度: {progress}%\n"

            if start_date:
                markdown += f"- 开始日期: {_format_date(start_date)}\n"

            if end_date:
                markdown += f"- 结束日期: {_format_date(end_date)}\n"

            markdown += "\n"

    # 添加任务
    if "tasks" in roadmap_data and roadmap_data["tasks"]:
        markdown += "## 任务\n\n"

        for task in roadmap_data["tasks"]:
            title = task.get("title", "")
            description = task.get("description", "")
            status = task.get("status", "")
            milestone = task.get("milestone", "")

            markdown += f"### {title}\n\n"

            if description:
                markdown += f"{description}\n\n"

            if status:
                markdown += f"- 状态: {status}\n"

            if milestone:
                markdown += f"- 里程碑: {milestone}\n"

            markdown += "\n"

    # 添加自定义内容
    if "content" in roadmap_data and roadmap_data["content"]:
        markdown += f"{roadmap_data['content']}\n"

    # 如果提供了输出路径，则写入文件
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

    return markdown


def _extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    从Markdown内容中提取frontmatter

    Args:
        content: Markdown内容

    Returns:
        Tuple[Dict[str, Any], str]: frontmatter数据和剩余的Markdown内容
    """
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

    if frontmatter_match:
        frontmatter_yaml = frontmatter_match.group(1)
        markdown_content = content[frontmatter_match.end() :]

        try:
            frontmatter_data = yaml.safe_load(frontmatter_yaml) or {}
        except yaml.YAMLError:
            frontmatter_data = {}

        return frontmatter_data, markdown_content
    else:
        return {}, content


def _parse_markdown_content(content: str) -> Dict[str, Any]:
    """
    解析Markdown内容，提取结构化数据

    Args:
        content: Markdown内容

    Returns:
        Dict[str, Any]: 解析后的数据
    """
    result = {"milestones": [], "tasks": [], "content": content}

    # 这里可以添加更复杂的解析逻辑，例如从Markdown中提取里程碑和任务信息
    # 由于这种解析很复杂，这里只提供一个简化的示例

    # 解析里程碑
    milestone_sections = re.finditer(r"##\s+(.*?)\n(.*?)(?=##|$)", content, re.DOTALL)

    for section in milestone_sections:
        section_title = section.group(1).strip()
        section_content = section.group(2).strip()

        if "里程碑" in section_title:
            # 解析里程碑数据
            milestone_matches = re.finditer(
                r"###\s+(.*?)\n(.*?)(?=###|$)", section_content, re.DOTALL
            )

            for milestone_match in milestone_matches:
                milestone_name = milestone_match.group(1).strip()
                milestone_content = milestone_match.group(2).strip()

                milestone = {"name": milestone_name, "description": "", "progress": 0}

                # 提取描述 (第一个非列表段落)
                desc_match = re.search(r"^(.*?)(?=\n-|\n\n|$)", milestone_content, re.DOTALL)
                if desc_match:
                    milestone["description"] = desc_match.group(1).strip()

                # 提取进度
                progress_match = re.search(r"进度:\s*(\d+)%", milestone_content)
                if progress_match:
                    milestone["progress"] = int(progress_match.group(1))

                # 提取日期
                start_date_match = re.search(r"开始日期:\s*(.*?)(?=\n|$)", milestone_content)
                if start_date_match:
                    milestone["start_date"] = start_date_match.group(1).strip()

                end_date_match = re.search(r"结束日期:\s*(.*?)(?=\n|$)", milestone_content)
                if end_date_match:
                    milestone["end_date"] = end_date_match.group(1).strip()

                result["milestones"].append(milestone)
        elif "任务" in section_title:
            # 解析任务数据
            task_matches = re.finditer(r"###\s+(.*?)\n(.*?)(?=###|$)", section_content, re.DOTALL)

            for task_match in task_matches:
                task_title = task_match.group(1).strip()
                task_content = task_match.group(2).strip()

                task = {"title": task_title, "description": ""}

                # 提取描述 (第一个非列表段落)
                desc_match = re.search(r"^(.*?)(?=\n-|\n\n|$)", task_content, re.DOTALL)
                if desc_match:
                    task["description"] = desc_match.group(1).strip()

                # 提取状态
                status_match = re.search(r"状态:\s*(.*?)(?=\n|$)", task_content)
                if status_match:
                    task["status"] = status_match.group(1).strip()

                # 提取里程碑
                milestone_match = re.search(r"里程碑:\s*(.*?)(?=\n|$)", task_content)
                if milestone_match:
                    task["milestone"] = milestone_match.group(1).strip()

                result["tasks"].append(task)

    return result


def _format_date(date_value: Any) -> str:
    """
    格式化日期值

    Args:
        date_value: 日期值

    Returns:
        str: 格式化后的日期字符串
    """
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    elif isinstance(date_value, str):
        try:
            date_obj = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            return date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return date_value
    else:
        return str(date_value)
