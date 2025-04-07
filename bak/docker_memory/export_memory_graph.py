import json
import os
from pathlib import Path


def create_markdown_file(entity, output_dir):
    """为每个实体创建一个 Markdown 文件"""
    filename = f"{entity['name'].replace('::', '_')}.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        # 写入 YAML front matter
        f.write("---\n")
        f.write(f'type: {entity["entityType"]}\n')
        f.write("---\n\n")

        # 写入标题
        f.write(f'# {entity["name"]}\n\n')

        # 写入观察内容
        f.write("## 观察\n\n")
        for obs in entity["observations"]:
            f.write(f"- {obs}\n")
        f.write("\n")

        # 为关系预留位置
        f.write("## 关系\n\n")
        f.write("```dataview\nLIST outgoing\nWHERE file.name = this.file.name\n```\n\n")
        f.write("```dataview\nLIST incoming\nWHERE file.name = this.file.name\n```\n")


def create_relations_file(relations, output_dir):
    """创建关系映射文件"""
    filepath = output_dir / "_relations.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# 知识图谱关系\n\n")
        for rel in relations:
            from_file = rel["from"].replace("::", "_")
            to_file = rel["to"].replace("::", "_")
            f.write(f'[[{from_file}]] {rel["relationType"]} [[{to_file}]]\n')


def main():
    # 创建输出目录
    output_dir = Path("/Users/chenyi/Public/VibeCopilot/docs/apply_rules.py")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取知识图谱数据
    with open("/Users/chenyi/Public/VibeCopilot/temp/memory_graph.json", "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    # 处理实体
    for entity in graph_data["entities"]:
        create_markdown_file(entity, output_dir)

    # 处理关系
    create_relations_file(graph_data["relations"], output_dir)

    print(f"已导出知识图谱到: {output_dir}")


if __name__ == "__main__":
    main()
