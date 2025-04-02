#!/usr/bin/env python3
"""
单文档解析测试工具
测试不同方法解析文档并提取实体关系
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests


def parse_with_openai(file_path, api_key):
    """使用OpenAI API解析文档

    Args:
        file_path: 文件路径
        api_key: OpenAI API密钥

    Returns:
        Dict: 解析结果
    """
    print("使用OpenAI模型解析...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # 构建提示词
    prompt = f"""分析以下Markdown文档，提取主要实体和关系。

文档路径: {file_path}

文档内容:
{content[:4000]}  # 限制长度

请执行以下任务:
1. 识别文档中的主要概念、实体、组件和技术
2. 确定这些实体之间的关系
3. 提取主要观察点和见解
4. 确定文档的类型和主题

以JSON格式返回结果，格式如下:
{{
  "document_type": "文档类型，如指南、架构、研究等",
  "main_topic": "文档的主要主题",
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型，如组件、概念、技术、人物等",
      "description": "简短描述"
    }}
  ],
  "relations": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称",
      "type": "关系类型，如包含、使用、依赖等"
    }}
  ],
  "observations": [
    "关键观察点1",
    "关键观察点2"
  ],
  "tags": ["标签1", "标签2"]
}}

只返回JSON，不要有其他文本。
"""

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个专业的文档分析工具，负责从文档中提取实体和关系。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()
        result = response.json()

        # 提取JSON部分
        content = result["choices"][0]["message"]["content"]
        json_start = content.find("{")
        json_end = content.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析JSON失败: {e}")
                print(f"原始内容: {content}")
                return {}
        else:
            print(f"无法从输出中提取JSON")
            return {}

    except Exception as e:
        print(f"调用OpenAI API失败: {e}")
        return {}


def parse_with_ollama(file_path, model="llama3"):
    """使用Ollama解析文档

    Args:
        file_path: 文件路径
        model: Ollama模型名称

    Returns:
        Dict: 解析结果
    """
    print(f"使用Ollama {model}模型解析...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = f"""分析以下Markdown文档，提取主要实体和关系。

文档路径: {file_path}

文档内容:
{content[:4000]}

请执行以下任务:
1. 识别文档中的主要概念、实体、组件和技术
2. 确定这些实体之间的关系
3. 提取主要观察点和见解
4. 确定文档的类型和主题

以JSON格式返回结果，格式如下:
{{
  "document_type": "文档类型，如指南、架构、研究等",
  "main_topic": "文档的主要主题",
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型，如组件、概念、技术、人物等",
      "description": "简短描述"
    }}
  ],
  "relations": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称",
      "type": "关系类型，如包含、使用、依赖等"
    }}
  ],
  "observations": [
    "关键观察点1",
    "关键观察点2"
  ],
  "tags": ["标签1", "标签2"]
}}

只返回JSON，不要有其他文本。
"""

    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt], capture_output=True, text=True, check=True
        )

        # 提取JSON部分
        output = result.stdout.strip()
        json_start = output.find("{")
        json_end = output.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = output[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析JSON失败: {e}")
                print(f"原始输出: {output}")
                return {}
        else:
            print(f"无法从输出中提取JSON")
            return {}

    except subprocess.CalledProcessError as e:
        print(f"调用Ollama失败: {e}")
        print(f"错误输出: {e.stderr}")
        return {}


def parse_with_regex(file_path):
    """使用正则表达式解析文档

    Args:
        file_path: 文件路径

    Returns:
        Dict: 解析结果
    """
    import re

    import frontmatter

    print("使用基础正则表达式解析...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析front matter
    post = frontmatter.loads(content)
    metadata = dict(post.metadata) if post.metadata else {}
    content_text = post.content

    # 提取标题
    title_match = re.search(r"^#\s+(.*?)$", content_text, re.MULTILINE)
    title = title_match.group(1) if title_match else Path(file_path).stem

    # 提取Wiki链接作为实体
    wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content_text)

    # 提取标准Markdown链接
    md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content_text)

    # 提取标题作为实体
    headings = re.findall(r"^##\s+(.*?)$", content_text, re.MULTILINE)

    # 提取标签
    tags = []
    if "tags" in metadata:
        if isinstance(metadata["tags"], list):
            tags.extend(metadata["tags"])
        elif isinstance(metadata["tags"], str):
            tags.append(metadata["tags"])

    # 从内容中提取#标签
    hash_tags = re.findall(r"#(\w+)", content_text)
    tags.extend(hash_tags)

    # 构建实体列表
    entities = []

    # 添加文档本身作为实体
    entities.append({"name": title, "type": "document", "description": "主文档"})

    # 添加Wiki链接作为实体
    for link in wiki_links:
        entities.append({"name": link, "type": "linked_document", "description": "通过Wiki链接引用的文档"})

    # 添加标题作为实体
    for heading in headings:
        entities.append({"name": heading, "type": "section", "description": "文档章节"})

    # 构建关系
    relations = []

    # 添加文档到Wiki链接的关系
    for link in wiki_links:
        relations.append({"source": title, "target": link, "type": "references"})

    # 添加文档到章节的关系
    for heading in headings:
        relations.append({"source": title, "target": heading, "type": "contains"})

    result = {
        "document_type": metadata.get("type", "unknown"),
        "main_topic": title,
        "entities": entities,
        "relations": relations,
        "observations": [],
        "tags": list(set(tags)),
    }

    return result


def print_visualization(result):
    """打印结果的可视化展示

    Args:
        result: 解析结果
    """
    print("\n" + "=" * 50)
    print(f"文档类型: {result.get('document_type', '未知')}")
    print(f"主题: {result.get('main_topic', '未知')}")
    print("=" * 50)

    print("\n实体:")
    print("-" * 50)
    for i, entity in enumerate(result.get("entities", []), 1):
        print(f"{i}. {entity.get('name', '未命名')} ({entity.get('type', '未知类型')})")
        if "description" in entity:
            print(f"   描述: {entity['description']}")

    print("\n关系:")
    print("-" * 50)
    for i, relation in enumerate(result.get("relations", []), 1):
        print(
            f"{i}. {relation.get('source', '?')} --[{relation.get('type', '关联')}]--> {relation.get('target', '?')}"
        )

    print("\n观察:")
    print("-" * 50)
    for i, obs in enumerate(result.get("observations", []), 1):
        print(f"{i}. {obs}")

    print("\n标签:")
    print("-" * 50)
    print(", ".join(result.get("tags", ["无标签"])))


def save_result(result, output_file):
    """保存结果到文件

    Args:
        result: 解析结果
        output_file: 输出文件路径
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="测试不同方法解析文档")
    parser.add_argument("file", help="要解析的Markdown文件路径")
    parser.add_argument(
        "--method",
        choices=["openai", "ollama", "regex"],
        default="regex",
        help="解析方法: openai, ollama, 或 regex (默认: regex)",
    )
    parser.add_argument("--model", default="llama3", help="Ollama模型名称 (默认: llama3)")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"错误: 文件不存在: {args.file}")
        sys.exit(1)

    print(f"解析文件: {args.file}")

    # 选择解析方法
    if args.method == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("错误: 未设置OPENAI_API_KEY环境变量")
            sys.exit(1)
        result = parse_with_openai(args.file, api_key)

    elif args.method == "ollama":
        result = parse_with_ollama(args.file, args.model)

    else:  # regex
        result = parse_with_regex(args.file)

    # 打印结果可视化
    print_visualization(result)

    # 保存结果
    if args.output:
        save_result(result, args.output)


if __name__ == "__main__":
    main()
