#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试memory命令与MemoryManager的集成

本脚本用于测试memory命令的功能是否正常，包括存储、检索、更新和删除功能。
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# 导入测试目标
from src.cli.commands.memory.memory_subcommands import (
    handle_create_subcommand,
    handle_delete_subcommand,
    handle_list_subcommand,
    handle_search_subcommand,
    handle_show_subcommand,
    handle_test_subcommand,
    handle_update_subcommand,
)


def test_memory_connection():
    """测试memory连接"""
    print("\n===== 测试连接 =====")
    success, message, data = handle_test_subcommand({})
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"数据: {data}")
    assert success, "连接测试失败"


def test_memory_create():
    """测试创建记忆"""
    print("\n===== 测试创建记忆 =====")
    args = {
        "title": "测试文档",
        "folder": "test",
        "content": "这是一个测试文档，用于测试memory命令与MemoryManager的集成。\n包含一些关键词：Python, 测试, 命令行接口, 向量存储。",
        "tags": "测试,Python,命令行",
    }
    success, message, data = handle_create_subcommand(args)
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"数据: {data}")
    assert success, "创建记忆失败"
    return data.get("permalink")


def test_memory_list():
    """测试列出记忆"""
    print("\n===== 测试列出记忆 =====")
    args = {"folder": "test"}
    success, message, data = handle_list_subcommand(args)
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"数据数量: {len(data)}")
    assert success, "列出记忆失败"
    assert len(data) > 0, "没有找到记忆"
    return data[0].get("permalink") if data else None


def test_memory_show(permalink):
    """测试显示记忆"""
    print(f"\n===== 测试显示记忆: {permalink} =====")
    args = {"path": permalink}
    success, message, data = handle_show_subcommand(args)
    print(f"成功: {success}")
    print(f"标题: {data.get('title', '未知')}")
    print(f"标签: {', '.join(data.get('tags', []))}")
    print(f"内容预览: {message[:100]}...")
    assert success, "显示记忆失败"
    return data


def test_memory_update(permalink):
    """测试更新记忆"""
    print(f"\n===== 测试更新记忆: {permalink} =====")
    args = {"path": permalink, "content": "这是更新后的内容。添加了一些新的信息，关于向量存储和自然语言处理。", "tags": "测试,Python,命令行,更新"}
    success, message, data = handle_update_subcommand(args)
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"数据: {data}")
    assert success, "更新记忆失败"


def test_memory_search():
    """测试搜索记忆"""
    print("\n===== 测试搜索记忆 =====")
    args = {"query": "向量存储 Python", "type": None}
    success, message, data = handle_search_subcommand(args)
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"结果数: {len(data)}")
    assert success, "搜索记忆失败"


def test_memory_delete(permalink):
    """测试删除记忆"""
    print(f"\n===== 测试删除记忆: {permalink} =====")
    args = {"path": permalink, "force": False}
    success, message, data = handle_delete_subcommand(args)
    print(f"成功: {success}")
    print(f"消息: {message}")
    print(f"数据: {data}")
    assert success, "删除记忆失败"


def main():
    """主测试函数"""
    try:
        print("开始测试memory命令与MemoryManager的集成")

        # 测试连接
        test_memory_connection()

        # 测试创建记忆
        permalink = test_memory_create()

        # 测试列出记忆
        if not permalink:
            permalink = test_memory_list()

        if permalink:
            # 测试显示记忆
            test_memory_show(permalink)

            # 测试更新记忆
            test_memory_update(permalink)

            # 测试搜索记忆
            test_memory_search()

            # 测试删除记忆
            test_memory_delete(permalink)

        print("\n所有测试完成！✅")

    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise


if __name__ == "__main__":
    main()
