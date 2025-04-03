"""
数据库命令行工具

提供数据库管理的命令行接口，包括初始化、同步和查询功能。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from .service import DatabaseService
from .sync import DataSynchronizer


def format_output(data: Any, format_type: str = "text") -> str:
    """
    格式化输出

    Args:
        data: 要格式化的数据
        format_type: 输出格式，支持text、json

    Returns:
        格式化后的字符串
    """
    if format_type == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)

    # 文本格式
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append("---")
                for key, value in item.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    else:
        return str(data)


def main():
    """命令行工具主函数"""
    parser = argparse.ArgumentParser(description="VibeCopilot数据库管理工具")

    # 全局参数
    parser.add_argument("--db-path", help="数据库文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 初始化命令
    init_parser = subparsers.add_parser("init", help="初始化数据库")

    # 同步命令
    sync_parser = subparsers.add_parser("sync", help="同步数据")
    sync_parser.add_argument(
        "--direction",
        choices=["to-fs", "from-fs", "to-yaml", "from-yaml", "to-github", "from-github"],
        required=True,
        help="同步方向",
    )
    sync_parser.add_argument("--target", help="同步目标，如文件路径")

    # 查询命令
    query_parser = subparsers.add_parser("query", help="查询数据")
    query_parser.add_argument(
        "--type", choices=["epic", "story", "task", "label"], required=True, help="查询类型"
    )
    query_parser.add_argument("--id", help="实体ID")
    query_parser.add_argument("--filters", help="过滤条件 (JSON格式)")

    # 创建命令
    create_parser = subparsers.add_parser("create", help="创建实体")
    create_parser.add_argument(
        "--type", choices=["epic", "story", "task", "label"], required=True, help="实体类型"
    )
    create_parser.add_argument("--data", required=True, help="实体数据 (JSON格式)")

    # 更新命令
    update_parser = subparsers.add_parser("update", help="更新实体")
    update_parser.add_argument(
        "--type", choices=["epic", "story", "task", "label"], required=True, help="实体类型"
    )
    update_parser.add_argument("--id", required=True, help="实体ID")
    update_parser.add_argument("--data", required=True, help="更新数据 (JSON格式)")

    # 删除命令
    delete_parser = subparsers.add_parser("delete", help="删除实体")
    delete_parser.add_argument(
        "--type", choices=["epic", "story", "task", "label"], required=True, help="实体类型"
    )
    delete_parser.add_argument("--id", required=True, help="实体ID")

    # 解析参数
    args = parser.parse_args()

    # 创建数据库服务
    db_service = DatabaseService(args.db_path)

    # 创建同步器
    synchronizer = DataSynchronizer(db_service)

    # 处理命令
    if args.command == "init":
        # 初始化数据库
        print("初始化数据库...")
        result = {"success": True, "message": "数据库初始化完成"}

    elif args.command == "sync":
        # 同步数据
        if args.direction == "to-fs":
            # 同步到文件系统
            story_count, task_count = synchronizer.sync_all_to_filesystem()
            result = {
                "success": True,
                "message": "数据已同步到文件系统",
                "story_count": story_count,
                "task_count": task_count,
            }

        elif args.direction == "from-fs":
            # 从文件系统同步
            story_count, task_count = synchronizer.sync_all_from_filesystem()
            result = {
                "success": True,
                "message": "从文件系统同步数据完成",
                "story_count": story_count,
                "task_count": task_count,
            }

        elif args.direction == "to-yaml":
            # 同步到YAML
            yaml_path = synchronizer.sync_to_roadmap_yaml(args.target)
            result = {
                "success": True,
                "message": "数据已同步到YAML",
                "yaml_path": yaml_path,
            }

        elif args.direction == "from-yaml":
            # 从YAML同步
            yaml_path = args.target
            epic_count, story_count, task_count = synchronizer.sync_from_roadmap_yaml(yaml_path)
            result = {
                "success": True,
                "message": "从YAML同步数据完成",
                "yaml_path": yaml_path,
                "epic_count": epic_count,
                "story_count": story_count,
                "task_count": task_count,
            }

        elif args.direction == "to-github":
            # 同步到GitHub
            result = synchronizer.sync_to_github()

        elif args.direction == "from-github":
            # 从GitHub同步
            result = synchronizer.sync_from_github()

    elif args.command == "query":
        # 查询数据
        entity_type = args.type
        entity_id = args.id

        # 解析过滤条件
        filters = None
        if args.filters:
            try:
                filters = json.loads(args.filters)
            except json.JSONDecodeError:
                print("错误: 过滤条件必须是有效的JSON格式")
                sys.exit(1)

        if entity_id:
            # 根据ID查询
            if entity_type == "epic":
                data = db_service.get_epic(entity_id)
            elif entity_type == "story":
                data = db_service.get_story(entity_id)
            elif entity_type == "task":
                data = db_service.get_task(entity_id)
            elif entity_type == "label":
                data = db_service.get_label(entity_id)

            if data:
                result = {
                    "success": True,
                    "message": f"查询{entity_type}成功",
                    "data": data,
                }
            else:
                result = {
                    "success": False,
                    "message": f"{entity_type}不存在: {entity_id}",
                }
        else:
            # 列表查询
            if entity_type == "epic":
                data = db_service.list_epics(filters)
            elif entity_type == "story":
                data = db_service.list_stories(filters)
            elif entity_type == "task":
                data = db_service.list_tasks(filters)
            elif entity_type == "label":
                data = db_service.list_labels()

            result = {
                "success": True,
                "message": f"查询{entity_type}列表成功",
                "count": len(data),
                "data": data,
            }

    elif args.command == "create":
        # 创建实体
        entity_type = args.type

        # 解析实体数据
        try:
            entity_data = json.loads(args.data)
        except json.JSONDecodeError:
            print("错误: 实体数据必须是有效的JSON格式")
            sys.exit(1)

        # 创建实体
        if entity_type == "epic":
            entity = db_service.create_epic(entity_data)
            entity_id = entity.id
        elif entity_type == "story":
            entity = db_service.create_story(entity_data)
            entity_id = entity.id
        elif entity_type == "task":
            labels = entity_data.pop("labels", None)
            entity = db_service.create_task(entity_data, labels)
            entity_id = entity.id
        elif entity_type == "label":
            entity = db_service.create_label(entity_data)
            entity_id = entity.id

        result = {
            "success": True,
            "message": f"创建{entity_type}成功",
            "id": entity_id,
        }

    elif args.command == "update":
        # 更新实体
        entity_type = args.type
        entity_id = args.id

        # 解析更新数据
        try:
            update_data = json.loads(args.data)
        except json.JSONDecodeError:
            print("错误: 更新数据必须是有效的JSON格式")
            sys.exit(1)

        # 更新实体
        if entity_type == "epic":
            data = db_service.update_epic(entity_id, update_data)
        elif entity_type == "story":
            data = db_service.update_story(entity_id, update_data)
        elif entity_type == "task":
            labels = update_data.pop("labels", None)
            data = db_service.update_task(entity_id, update_data, labels)
        elif entity_type == "label":
            # 标签暂不支持更新
            data = None

        if data:
            result = {
                "success": True,
                "message": f"更新{entity_type}成功",
                "data": data,
            }
        else:
            result = {
                "success": False,
                "message": f"更新{entity_type}失败，实体不存在或无法更新",
            }

    elif args.command == "delete":
        # 删除实体
        entity_type = args.type
        entity_id = args.id

        # 删除实体
        if entity_type == "epic":
            success = db_service.delete_epic(entity_id)
        elif entity_type == "story":
            success = db_service.delete_story(entity_id)
        elif entity_type == "task":
            success = db_service.delete_task(entity_id)
        elif entity_type == "label":
            # 标签暂不支持删除
            success = False

        if success:
            result = {
                "success": True,
                "message": f"删除{entity_type}成功",
            }
        else:
            result = {
                "success": False,
                "message": f"删除{entity_type}失败，实体不存在或无法删除",
            }
    else:
        # 没有指定命令
        parser.print_help()
        sys.exit(0)

    # 输出结果
    print(format_output(result, args.format))

    # 返回状态码
    if result.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
