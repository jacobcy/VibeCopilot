#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Basic Memory工具直接测试

该脚本用于直接测试MCP Basic Memory工具的功能，跳过BasicMemoryAdapter层。
"""

import argparse
import json
import sys


def test_write_note():
    """测试写入笔记"""
    try:
        # 直接导入MCP工具
        from mcp_basic_memory_write_note import mcp_basic_memory_write_note

        # 写入测试笔记
        content = (
            "这是一个直接使用MCP Basic Memory工具创建的测试笔记。\n" "如果你看到这条笔记，说明MCP工具集成成功了！\n\n" "- 创建时间: 2023-06-20\n" "- 目的: 验证MCP工具可用性\n" "- 标签: #测试 #MCP #直接访问"
        )

        result = mcp_basic_memory_write_note(title="MCP直接访问测试", content=content, folder="vibecopilot/test_direct", tags="test,mcp,direct")

        print("✅ 写入笔记成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get("permalink") if result else None
    except ImportError:
        print("❌ 无法导入MCP工具，确保在Cursor环境中运行")
        return None
    except Exception as e:
        print(f"❌ 写入笔记失败: {str(e)}")
        return None


def test_read_note(permalink):
    """测试读取笔记"""
    try:
        # 直接导入MCP工具
        from mcp_basic_memory_read_note import mcp_basic_memory_read_note

        # 读取笔记
        result = mcp_basic_memory_read_note(identifier=permalink)

        print("\n✅ 读取笔记成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except ImportError:
        print("❌ 无法导入MCP工具，确保在Cursor环境中运行")
        return False
    except Exception as e:
        print(f"❌ 读取笔记失败: {str(e)}")
        return False


def test_search_notes():
    """测试搜索笔记"""
    try:
        # 直接导入MCP工具
        from mcp_basic_memory_search_notes import mcp_basic_memory_search_notes

        # 搜索笔记
        result = mcp_basic_memory_search_notes(query="MCP直接访问测试")

        print("\n✅ 搜索笔记成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except ImportError:
        print("❌ 无法导入MCP工具，确保在Cursor环境中运行")
        return False
    except Exception as e:
        print(f"❌ 搜索笔记失败: {str(e)}")
        return False


def test_delete_note(permalink):
    """测试删除笔记"""
    try:
        # 直接导入MCP工具
        from mcp_basic_memory_delete_note import mcp_basic_memory_delete_note

        # 删除笔记
        result = mcp_basic_memory_delete_note(identifier=permalink)

        print("\n✅ 删除笔记成功:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except ImportError:
        print("❌ 无法导入MCP工具，确保在Cursor环境中运行")
        return False
    except Exception as e:
        print(f"❌ 删除笔记失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Basic Memory工具直接测试")
    parser.add_argument("--operation", choices=["write", "read", "search", "delete", "all"], default="all", help="要测试的操作")
    parser.add_argument("--permalink", help="笔记的永久链接")

    args = parser.parse_args()

    # 执行测试
    permalink = args.permalink

    if args.operation == "write" or args.operation == "all":
        permalink = test_write_note() or permalink

    if permalink:
        if args.operation == "read" or args.operation == "all":
            test_read_note(permalink)

        if args.operation == "search" or args.operation == "all":
            test_search_notes()

        if args.operation == "delete" or args.operation == "all":
            test_delete_note(permalink)
    else:
        print("❌ 未提供永久链接，无法执行读取/删除操作")
        if args.operation == "search" or args.operation == "all":
            test_search_notes()


if __name__ == "__main__":
    main()
