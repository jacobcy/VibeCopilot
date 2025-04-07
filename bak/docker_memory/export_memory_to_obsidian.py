import json
import os
from pathlib import Path


def create_markdown_file(entity, output_dir):
    """为每个实体创建一个 Markdown 文件"""
    # 将::替换为_以创建有效的文件名
    filename = f"{entity['name'].replace('::', '_')}.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        # 写入 YAML front matter
        f.write("---\n")
        f.write(f'type: {entity["entityType"]}\n')
        f.write(f'name: {entity["name"]}\n')
        f.write("---\n\n")

        # 写入标题
        f.write(f'# {entity["name"]}\n\n')

        # 写入观察内容
        f.write("## 观察\n\n")
        for obs in entity["observations"]:
            f.write(f"- {obs}\n")
        f.write("\n")

        # 添加关系视图
        f.write("## 关系\n\n")
        f.write("```dataview\nLIST outgoing\nWHERE file.name = this.file.name\n```\n\n")
        f.write("```dataview\nLIST incoming\nWHERE file.name = this.file.name\n```\n")


def create_relations_file(relations, output_dir):
    """创建关系映射文件"""
    filepath = output_dir / "_relations.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# 知识图谱关系总览\n\n")
        f.write("## 所有关系\n\n")
        for rel in relations:
            from_file = rel["from"].replace("::", "_")
            to_file = rel["to"].replace("::", "_")
            f.write(f'- [[{from_file}]] {rel["relationType"]} [[{to_file}]]\n')


def create_index_file(entities, output_dir):
    """创建索引文件"""
    filepath = output_dir / "index.md"

    # 按实体类型分组
    entity_types = {}
    for entity in entities:
        etype = entity["entityType"]
        if etype not in entity_types:
            entity_types[etype] = []
        entity_types[etype].append(entity)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# 知识图谱索引\n\n")

        for etype, ents in sorted(entity_types.items()):
            f.write(f"## {etype}\n\n")
            for entity in sorted(ents, key=lambda x: x["name"]):
                name = entity["name"].replace("::", "_")
                f.write(f"- [[{name}]]\n")
            f.write("\n")


def main():
    try:
        # 设置输出目录
        output_dir = Path("/Users/chenyi/Public/VibeCopilot/.ai/knowledge_graph")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 使用完整的图谱数据
        graph_data = {
            "entities": [
                {
                    "type": "entity",
                    "name": "VibeCopilot",
                    "entityType": "project",
                    "observations": [
                        "项目名称: VibeCopilot",
                        "类型: AI工具整合平台",
                        "目标: 连接各工具生态系统的中枢",
                        "当前阶段: 规划和原型设计阶段",
                    ],
                },
                {
                    "type": "entity",
                    "name": "VibeCopilot::architecture",
                    "entityType": "documentation_category",
                    "observations": [
                        "类型: 架构文档集合",
                        "创建时间: 2024-04-01",
                        "文档数量: 11个核心文档",
                        "文档路径: /docs/dev/architecture/",
                    ],
                },
            ],
            "relations": [
                {
                    "type": "relation",
                    "from": "VibeCopilot",
                    "to": "VibeCopilot::architecture",
                    "relationType": "包含",
                }
            ],
        }

        # 处理实体
        print(f"创建实体文件... (共{len(graph_data['entities'])}个实体)")
        for entity in graph_data["entities"]:
            create_markdown_file(entity, output_dir)

        # 处理关系
        print(f"创建关系文件... (共{len(graph_data['relations'])}个关系)")
        create_relations_file(graph_data["relations"], output_dir)

        # 创建索引
        print("创建索引文件...")
        create_index_file(graph_data["entities"], output_dir)

        print(f"\n✨ 导出完成！文件保存在: {output_dir}")
        print("\n📝 使用说明:")
        print("1. 使用Obsidian打开上述目录")
        print("2. 启用以下插件:")
        print("   - Graph View (查看知识图谱可视化)")
        print("   - Dataview (查询和过滤数据)")
        print("   - Tags (使用标签进行分类)")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        raise


if __name__ == "__main__":
    main()
