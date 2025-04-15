#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库处理器

提供知识库内容管理的处理函数，使用MemoryManager实现，同时整合SQLite和向量库的数据。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from src.db import get_session
from src.db.repositories.memory_item_repository import MemoryItemRepository

# 导入MemoryManager
from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# 创建全局内存管理器实例
memory_manager = MemoryManager()
session = get_session()
memory_item_repo = MemoryItemRepository(session)


def handle_list_notes(folder: str = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理列出知识库内容请求

    Args:
        folder: 筛选特定目录的内容（可选）

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    try:
        logger.info(f"列出知识库内容: {'全部' if folder is None else f'目录: {folder}'}")

        # 使用MemoryManager列出所有记忆
        result = asyncio.run(memory_manager.list_memories(folder=folder, limit=10))

        if not result.get("success", False):
            return False, result.get("message", "列出知识库内容失败"), []

        memories = result.get("memories", [])

        # 处理结果
        formatted_results = []
        for memory in memories:
            formatted_result = {
                "permalink": memory.get("permalink", ""),
                "title": memory.get("title", "未命名文档"),
                "folder": folder or memory_manager.default_folder,
                "created_at": memory.get("created_at", "未知时间"),
                "updated_at": memory.get("updated_at", "未知时间"),
                "tags": memory.get("tags", "").split(",") if memory.get("tags") else [],
                "memory_item_id": memory.get("memory_item_id", None),
                "entity_count": memory.get("entity_count", 0),
                "relation_count": memory.get("relation_count", 0),
                "observation_count": memory.get("observation_count", 0),
            }
            formatted_results.append(formatted_result)

        if not formatted_results:
            return True, "知识库中没有找到内容" + (f"（目录: {folder}）" if folder else ""), []

        # 格式化输出
        formatted_output = "\n".join(
            [
                f"📄 {r['title']} - [{r['folder']}] - {', '.join(r['tags']) if r['tags'] else '无标签'} - {r['updated_at'].split('T')[0] if 'T' in str(r['updated_at']) else r['updated_at']}"
                for r in formatted_results
            ]
        )

        summary = f"找到 {len(formatted_results)} 个文档:\n\n{formatted_output}"

        return True, summary, formatted_results
    except Exception as e:
        error_message = f"列出知识库内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, []


def handle_write_note(content: str, title: str, folder: str, tags: str = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理写入知识库请求

    Args:
        content: 要保存的内容
        title: 文档标题
        folder: 存储目录
        tags: 标签列表（逗号分隔）

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    try:
        logger.info(f"写入知识库: {title} 到 {folder}")

        # 使用MemoryManager存储记忆
        result = asyncio.run(memory_manager.store_memory(content=content, title=title, tags=tags, folder=folder))

        if not result.get("success", False):
            return False, result.get("message", "保存内容失败"), {}

        # 构建结果
        formatted_result = {
            "permalink": result.get("permalink", ""),
            "title": title,
            "folder": result.get("folder", folder),
            "tags": tags.split(",") if tags else [],
            "word_count": len(content.split()),
            "entity_count": result.get("entity_count", 0),
            "relation_count": result.get("relation_count", 0),
            "observation_count": result.get("observation_count", 0),
            "memory_item_id": result.get("memory_item_id", None),
        }

        success_message = (
            f"📝 内容已保存!\n"
            f"ID: {formatted_result['memory_item_id']}\n"
            f"存储位置: {formatted_result['folder']}/{title}.md\n"
            f"标签: {tags or '无'}\n"
            f"字数: {formatted_result['word_count']}字\n"
            f"实体数: {formatted_result['entity_count']}\n"
            f"关系数: {formatted_result['relation_count']}\n"
            f"观察数: {formatted_result['observation_count']}"
        )

        return True, success_message, formatted_result
    except Exception as e:
        error_message = f"保存内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def handle_read_note(identifier: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理读取知识库请求

    Args:
        identifier: 文档路径、标识符或ID

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    try:
        logger.info(f"读取知识库: {identifier}")

        # 判断是permalink还是memory_item_id
        memory_item = None
        result = None

        # 尝试将identifier解析为整数
        try:
            memory_item_id = int(identifier)
            memory_item = memory_item_repo.get_by_id(memory_item_id)
        except (ValueError, TypeError):
            # 不是整数ID，当作permalink处理
            pass

        if memory_item:
            # 通过MemoryItem构建结果
            logger.info(f"找到MemoryItem: ID={memory_item.id}")
            permalink = memory_item.permalink

            # 如果有permalink，尝试从向量库获取更多数据
            if permalink:
                result = asyncio.run(memory_manager.get_memory_by_id(permalink))

            if not result or not result.get("success", False):
                # 直接使用MemoryItem数据
                formatted_result = {
                    "permalink": memory_item.permalink,
                    "title": memory_item.title,
                    "content": memory_item.content,
                    "created_at": memory_item.created_at.isoformat() if memory_item.created_at else None,
                    "updated_at": memory_item.updated_at.isoformat() if memory_item.updated_at else None,
                    "folder": memory_item.folder,
                    "tags": memory_item.tags.split(",") if memory_item.tags else [],
                    "memory_item_id": memory_item.id,
                    "entity_count": memory_item.entity_count,
                    "relation_count": memory_item.relation_count,
                    "observation_count": memory_item.observation_count,
                }
                return True, memory_item.content, formatted_result

        # 使用MemoryManager获取记忆
        if not result:
            logger.info(f"开始调用memory_manager.get_memory_by_id，参数: {identifier}")
            result = asyncio.run(memory_manager.get_memory_by_id(identifier))

        # 记录结果以进行诊断
        logger.info(f"获取记忆结果: success={result.get('success', False)}, message={result.get('message', 'N/A')}")

        if not result.get("success", False):
            error_msg = result.get("message", f"未找到文档: {identifier}")
            logger.error(f"获取记忆失败: {error_msg}")
            return False, error_msg, {}

        # 获取记忆数据
        memory = result.get("memory", {})
        metadata = memory.get("metadata", {})
        content = memory.get("content", "")

        # 构建格式化的结果
        formatted_result = {
            "permalink": memory.get("permalink", ""),
            "title": memory.get("title", "未命名文档"),
            "content": content,
            "created_at": metadata.get("created_at", "未知时间"),
            "updated_at": metadata.get("updated_at", "未知时间"),
            "folder": metadata.get("folder", memory_manager.default_folder),
            "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
            "memory_item_id": memory.get("memory_item_id"),
            "entity_count": metadata.get("entity_count", 0),
            "relation_count": metadata.get("relation_count", 0),
            "observation_count": metadata.get("observation_count", 0),
        }

        return True, content, formatted_result
    except Exception as e:
        error_message = f"读取内容失败: {str(e)}"
        logger.error(error_message, exc_info=True)  # 添加异常堆栈
        return False, error_message, {}


def handle_update_note(identifier: str, content: str, tags: str = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理更新知识库内容请求

    Args:
        identifier: 文档路径、标识符或ID
        content: 更新后的内容
        tags: 更新的标签（逗号分隔）

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    try:
        logger.info(f"更新知识库内容: {identifier}")

        # 首先读取现有内容
        success, _, existing_data = handle_read_note(identifier)
        if not success:
            return False, f"无法找到要更新的文档: {identifier}", {}

        # 获取permalink
        permalink = existing_data.get("permalink")
        if not permalink:
            return False, "更新失败: 无法获取记忆的永久链接", {}

        # 删除原记忆
        delete_result = asyncio.run(memory_manager.delete_memory(permalink))
        if not delete_result.get("success", False):
            return False, f"更新失败: 无法删除原记忆: {delete_result.get('message')}", {}

        # 获取原文档的folder和title
        folder = existing_data.get("folder", memory_manager.default_folder)
        title = existing_data.get("title", "未知标题")

        # 创建新记忆
        result = asyncio.run(
            memory_manager.store_memory(content=content, title=title, tags=tags or ",".join(existing_data.get("tags", [])), folder=folder)
        )

        if not result.get("success", False):
            return False, result.get("message", "更新内容失败"), {}

        # 构建结果
        formatted_result = {
            "permalink": result.get("permalink", ""),
            "title": title,
            "folder": result.get("folder", folder),
            "tags": tags.split(",") if tags else existing_data.get("tags", []),
            "word_count": len(content.split()),
            "entity_count": result.get("entity_count", 0),
            "relation_count": result.get("relation_count", 0),
            "observation_count": result.get("observation_count", 0),
            "memory_item_id": result.get("memory_item_id"),
        }

        success_message = (
            f"📝 内容已更新!\n"
            f"文档: {formatted_result['title']}\n"
            f"ID: {formatted_result['memory_item_id']}\n"
            f"存储位置: {formatted_result['folder']}\n"
            f"标签: {', '.join(formatted_result['tags']) if formatted_result['tags'] else '无'}\n"
            f"字数: {formatted_result['word_count']}字\n"
            f"实体数: {formatted_result['entity_count']}\n"
            f"关系数: {formatted_result['relation_count']}\n"
            f"观察数: {formatted_result['observation_count']}"
        )

        return True, success_message, formatted_result
    except Exception as e:
        error_message = f"更新内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def handle_delete_note(identifier: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理删除知识库内容请求

    Args:
        identifier: 文档路径、标识符或ID
        force: 是否强制删除

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    try:
        logger.info(f"删除知识库内容: {identifier}, 强制: {force}")

        # 判断是permalink还是memory_item_id
        permalink = None
        title = "未知文档"
        memory_item = None

        # 尝试将identifier解析为整数
        try:
            memory_item_id = int(identifier)
            memory_item = memory_item_repo.get_by_id(memory_item_id)
        except (ValueError, TypeError):
            # 不是整数ID，当作permalink处理
            permalink = identifier

        if memory_item:
            # 从MemoryItem获取信息
            permalink = memory_item.permalink
            title = memory_item.title

        if not permalink and not memory_item:
            if not force:
                return False, f"无法识别要删除的文档标识符: {identifier}", {}
            permalink = identifier  # 强制模式下尝试使用原始标识符

        # 如果有permalink，先尝试从向量库删除
        if permalink:
            result = asyncio.run(memory_manager.delete_memory(permalink))
            # 记录结果，但不影响后续流程
            if not result.get("success", False):
                logger.warning(f"从向量库删除失败: {result.get('message', '未知错误')}")

        # 如果有memory_item，从SQLite删除
        success = False
        if memory_item:
            success = memory_item_repo.delete(memory_item.id)
            if not success:
                logger.warning(f"从SQLite删除失败: ID={memory_item.id}")

        # 强制模式下，无论是否真正删除成功都返回成功
        if force:
            return True, f"强制删除完成: {title} ({identifier})", {"permalink": permalink, "memory_item_id": memory_item.id if memory_item else None}

        # 非强制模式下，至少有一个删除成功就算成功
        if permalink and not memory_item:
            success = True

        if success:
            success_message = f"🗑️ 文档已删除: {title}"
            return True, success_message, {"permalink": permalink, "title": title, "memory_item_id": memory_item.id if memory_item else None}
        else:
            return False, f"删除文档失败: {identifier}", {}
    except Exception as e:
        if force:
            return True, f"强制删除完成（出现错误）: {identifier}, 错误: {str(e)}", {"identifier": identifier}

        error_message = f"删除内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def handle_search_notes(query: str, content_type: str = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理搜索子命令

    Args:
        query: 搜索关键词
        content_type: 内容类型过滤

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    try:
        logger.info(f"搜索知识库: {query}, 类型: {content_type or '全部'}")

        # 使用MemoryManager搜索记忆
        result = asyncio.run(memory_manager.retrieve_memory(query=query, limit=5))

        if not result.get("success", False):
            return False, result.get("message", "搜索失败"), []

        memories = result.get("memories", [])

        # 处理结果
        search_results = []
        for memory in memories:
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})

            # 生成预览文本（最多200个字符）
            preview = content
            if len(preview) > 200:
                preview = preview[:197] + "..."

            search_result = {
                "title": memory.get("title", "未命名文档"),
                "preview": preview,
                "permalink": memory.get("permalink", ""),
                "score": memory.get("score", 0),
                "folder": metadata.get("folder", memory_manager.default_folder),
                "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                "updated_at": metadata.get("updated_at", "未知时间"),
                "memory_item_id": memory.get("memory_item_id"),
                "entity_count": metadata.get("entity_count", 0),
                "relation_count": metadata.get("relation_count", 0),
            }
            search_results.append(search_result)

        if not search_results:
            # 在SQLite中尝试基本搜索
            logger.info("向量库搜索无结果，尝试在SQLite中搜索")
            memory_items = memory_item_repo.search_by_content(query)

            for item in memory_items:
                # 生成预览文本（最多200个字符）
                preview = item.content
                if len(preview) > 200:
                    preview = preview[:197] + "..."

                search_results.append(
                    {
                        "title": item.title,
                        "preview": preview,
                        "permalink": item.permalink,
                        "score": 0.5,  # 给SQLite结果一个默认分数
                        "folder": item.folder,
                        "tags": item.tags.split(",") if item.tags else [],
                        "updated_at": item.updated_at.isoformat() if item.updated_at else "未知时间",
                        "memory_item_id": item.id,
                        "entity_count": item.entity_count,
                        "relation_count": item.relation_count,
                    }
                )

            if not search_results:
                return True, f"未找到匹配的内容: {query}", []

        # 格式化输出
        formatted_output = "\n\n".join(
            [
                f"### 📄 {r['title']} (相关度: {r['score']:.2f})\n"
                f"ID: {r['memory_item_id'] or '无'}\n"
                f"路径: {r['permalink']}\n"
                f"标签: {', '.join(r['tags']) if r['tags'] else '无'}\n"
                f"预览: {r['preview']}"
                for r in search_results
            ]
        )

        summary = f"搜索结果: {query}\n找到 {len(search_results)} 个相关文档:\n\n{formatted_output}"

        return True, summary, search_results
    except Exception as e:
        error_message = f"搜索失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, []


def handle_test_connection() -> Tuple[bool, str, Dict[str, Any]]:
    """
    测试知识库连接

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    try:
        # 测试向量库连接
        vector_store_result = asyncio.run(memory_manager.list_memories(limit=1))
        vector_store_success = vector_store_result.get("success", False)
        vector_store_count = len(vector_store_result.get("memories", []))

        # 测试SQLite连接
        sqlite_items = memory_item_repo.get_all(limit=1)
        sqlite_success = sqlite_items is not None
        sqlite_count = len(sqlite_items) if sqlite_items else 0

        if vector_store_success and sqlite_success:
            return (
                True,
                f"连接成功！向量库中有 {vector_store_count} 条记忆，SQLite中有 {sqlite_count} 条记录。",
                {"vector_store_count": vector_store_count, "sqlite_count": sqlite_count},
            )
        elif vector_store_success:
            return True, f"向量库连接成功，但SQLite连接失败。向量库中有 {vector_store_count} 条记忆。", {"vector_store_count": vector_store_count}
        elif sqlite_success:
            return True, f"SQLite连接成功，但向量库连接失败。SQLite中有 {sqlite_count} 条记录。", {"sqlite_count": sqlite_count}
        else:
            return False, "向量库和SQLite连接均失败。", {}
    except Exception as e:
        error_message = f"连接测试失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}
