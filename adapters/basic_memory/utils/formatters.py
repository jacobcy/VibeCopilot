"""
格式化工具函数
提供实体格式转换和可视化功能
"""

from typing import Any, Dict, List


def convert_to_entity_format(parsed_result: Dict[str, Any]) -> Dict[str, Any]:
    """将content_parser的结果转换为实体关系格式

    Args:
        parsed_result: 内容解析器的结果

    Returns:
        Dict: 转换后的实体关系结构
    """
    # 如果已经是实体关系格式，直接返回
    if "entities" in parsed_result and "relations" in parsed_result:
        return parsed_result

    # 从文档结构中提取实体关系
    result = {
        "document_type": "document",
        "main_topic": parsed_result.get("title", ""),
        "entities": [],
        "relations": [],
        "observations": [],
        "tags": [],
    }

    # 添加文档本身作为实体
    result["entities"].append(
        {
            "name": parsed_result.get("title", ""),
            "type": "document",
            "description": parsed_result.get("description", ""),
        }
    )

    # 从块中提取实体和观察
    for block in parsed_result.get("blocks", []):
        if block["type"] == "heading":
            # 添加标题作为实体
            result["entities"].append(
                {
                    "name": block["content"],
                    "type": "section",
                    "description": f"Level {block.get('level', 1)} heading",
                }
            )
            # 添加文档与章节的关系
            result["relations"].append(
                {
                    "source": parsed_result.get("title", ""),
                    "target": block["content"],
                    "type": "contains",
                }
            )
        elif block["type"] == "text":
            # 将文本块添加为观察
            result["observations"].append(block["content"])

    return result


def print_entity_visualization(result: Dict[str, Any]) -> None:
    """打印实体数据的可视化展示

    Args:
        result: 实体关系数据
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
        if len(obs) > 100:
            print(f"{i}. {obs[:100]}...")
        else:
            print(f"{i}. {obs}")

    print("\n标签:")
    print("-" * 50)
    print(", ".join(result.get("tags", ["无标签"])))
