#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存 CRUD 服务模块

提供与 MemoryItem 相关的 CRUD 操作，协调 BasicMemoryWrapper 和 MemoryItemRepository。
"""

import logging
import os
import pathlib
from typing import Any, Dict, Optional, Tuple

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.db.session_manager import session_scope
from src.memory.tools.basic_memory_wrapper import BasicMemoryWrapper
from src.parsing.processors.document_processor import DocumentProcessor

doc_processor = DocumentProcessor()  # Initialize processor once for reuse
logger = logging.getLogger(__name__)

# SyncStatus enum can be used here in the service layer
from src.status.enums import SyncStatus

# ===== 路径与标识符处理 (服务层逻辑) =====


def _derive_identifier_from_permalink(permalink: str) -> Optional[str]:
    """从 permalink 提取 identifier"""
    prefix = "memory://"
    if permalink.startswith(prefix):
        return permalink[len(prefix) :]
    logger.warning(f"无法从无效的 permalink '{permalink}' 派生 identifier")
    return None


def _get_identifier_from_permalink(permalink: Optional[str]) -> Optional[str]:
    """从 permalink 提取标识符（去掉前缀）"""
    if not permalink:
        return None
    prefix = "memory://"
    if permalink.startswith(prefix):
        return permalink[len(prefix) :]
    return permalink  # 如果没有前缀，直接返回


def _get_file_path(memory_root: pathlib.Path, identifier: str) -> pathlib.Path:
    """根据 memory_root 和 identifier 生成文件路径 (保持不变)"""
    # TODO: 处理 identifier 中可能存在的非法路径字符
    safe_identifier = identifier  # .replace("..", "") # 基本的安全处理
    return memory_root / f"{safe_identifier}.md"


# ===== 摘要生成 (服务层逻辑) =====


def _generate_summary(content: str, title: Optional[str] = None, fallback_text: Optional[str] = None, max_length: int = 150) -> str:
    """生成文档摘要，包含回退逻辑"""
    try:
        summary = doc_processor.generate_document_summary(content, max_length=max_length)
        logger.info(f"使用LLM生成摘要: {summary[:30]}...")
        return summary
    except Exception as e:
        logger.warning(f"使用LLM生成摘要失败: {e}")
        # Fallback logic
        if title:
            return title[:max_length]
        if fallback_text:
            return fallback_text[:max_length]
        if content:
            # Simple truncate as last resort
            return content[:max_length] + "..." if len(content) > max_length else content
        return "无可用摘要"


# ===== CRUD 操作 (服务层逻辑) =====


def execute_create_note(
    content: str,
    title: str,
    folder: str,
    tags: Optional[str],
    repo: MemoryItemRepository,
    basic_memory: BasicMemoryWrapper,
    memory_root: pathlib.Path,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    执行创建笔记的操作:
    1. 调用 Wrapper 创建远程笔记。
    2. 生成摘要。
    3. 调用 Repository 创建或更新本地索引记录。
    """
    logger.info(f"执行创建笔记: '{title}' 到 '{folder}'")

    # --- 1. 调用 Wrapper ---
    if title.endswith(".md"):
        title = title[:-3]  # Normalize title
    if not folder:
        folder = "notes"
    folder = folder.strip("/")

    try:
        tool_success, tool_msg, tool_data = basic_memory.write_note(content, title, folder, tags)
    except Exception as e:
        logger.exception(f"调用 basic_memory.write_note 创建笔记时出错: {e}")
        return False, f"知识库工具调用失败: {str(e)}", {}

    if not tool_success:
        logger.error(f"Wrapper (write_note) 创建失败: {tool_msg}")
        return False, f"知识库工具创建失败: {tool_msg}", tool_data

    permalink = tool_data.get("permalink")
    if not permalink:
        logger.error("Wrapper (write_note) 未能返回 permalink")
        return False, "知识库工具未返回有效标识，无法同步数据库", tool_data

    # --- 2. 准备数据 & 生成摘要 ---
    identifier = _get_identifier_from_permalink(permalink)
    if not identifier:
        logger.error(f"无法从 permalink '{permalink}' 获取有效标识符")
        return False, "无法确定内部标识符，同步数据库失败", tool_data

    file_path = _get_file_path(memory_root, identifier)
    summary = _generate_summary(content, title=title, fallback_text=permalink)

    # --- 3. 同步数据库 ---
    db_data = {
        "title": title,
        "folder": folder,
        "summary": summary,
        "tags": tags,
        "permalink": permalink,  # 使用 basic-memory 返回的 permalink
        "file_path": str(file_path),
        "sync_status": SyncStatus.SYNCED.name,  # 通过 wrapper 创建，假定已同步
        "is_deleted": False,  # 创建或更新时确保记录为未删除状态
    }

    try:
        with session_scope() as session:
            # 查找可能存在的记录（包括已删除的记录）
            existing_item = repo.find_by_permalink(session, permalink, include_deleted=True)
            if existing_item:
                # 记录已存在，更新它（包括可能是软删除的记录）
                if existing_item.is_deleted:
                    logger.info(f"找到已删除的记录（ID={existing_item.id}），重新激活")

                # 更新所有字段
                for key, value in db_data.items():
                    setattr(existing_item, key, value)
                session.commit()
                db_item = existing_item
            else:
                # 没有找到记录，创建新记录
                db_item = repo.create(session, db_data)

            final_message = f"笔记 '{title}' 创建成功.\n永久链接: {permalink}"
            logger.info(f"笔记创建并记录DB成功: permalink='{permalink}' (id={db_item.id})")
            # Return consistent structure
            return_data = {
                "permalink": permalink,
                "identifier": identifier,  # Return derived identifier for context
                "db_id": db_item.id,
                "summary": summary,
                "title": title,
                "folder": folder,
            }
            return True, final_message, return_data
    except Exception as e:
        logger.exception(f"添加或更新数据库记录失败 (permalink={permalink}): {e}")
        error_msg = f"知识库创建成功，但同步数据库失败: {str(e)}"
        # Even if DB sync fails, the remote note was created
        return True, error_msg, {"permalink": permalink, "identifier": identifier, "error": "db_sync_failed"}


def execute_read_note(
    path_or_permalink: str,  # Accepts permalink or identifier
    repo: MemoryItemRepository,
    basic_memory: BasicMemoryWrapper,
    memory_root: pathlib.Path,  # memory_root 可能不再需要，如果文件路径由repo管理
    use_local_cache_for_metadata: bool = True,  # 更准确的命名
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    执行读取笔记的操作:
    1. 解析输入，确定 permalink。
    2. (可选) 尝试从本地 DB 查找元数据。
    3. 调用 Wrapper 读取远程笔记获取完整内容。
    4. (可选) 将获取的远程内容生成摘要并更新本地 DB 缓存。
    5. 合并元数据和内容返回。
    """
    logger.debug(f"执行读取笔记: input='{path_or_permalink}', use_local_metadata={use_local_cache_for_metadata}")

    # --- 1. 解析输入 ---
    target_permalink: Optional[str] = None
    target_identifier: Optional[str] = None
    local_metadata: Optional[Dict[str, Any]] = None

    if path_or_permalink.startswith("memory://"):
        target_permalink = path_or_permalink
        target_identifier = _get_identifier_from_permalink(target_permalink)
    else:
        # 输入是标识符，构造 permalink
        target_identifier = path_or_permalink
        target_permalink = f"memory://{target_identifier}"
        logger.debug(f"输入被视为标识符，构造的 permalink: {target_permalink}")

    if not target_permalink:
        return False, f"无法从输入 '{path_or_permalink}' 解析有效的 permalink", {}

    # --- 2. 尝试本地元数据查找 ---
    if use_local_cache_for_metadata:
        try:
            with session_scope() as session:
                item = repo.find_by_permalink(session, target_permalink, include_deleted=False)
                if item:
                    logger.info(f"从本地数据库找到元数据: permalink='{item.permalink}'")
                    local_metadata = {
                        "id": item.id,
                        "title": item.title,
                        "folder": item.folder,
                        "tags": item.tags,
                        "permalink": item.permalink,
                        "summary": item.summary,
                        "file_path": item.file_path,
                        "source": "local_metadata",  # Indicate metadata source
                    }
                    # 确认 identifier
                    target_identifier = target_identifier or _get_identifier_from_permalink(str(item.permalink))
                else:
                    logger.debug("本地数据库未找到或已删除")
        except Exception as e:
            logger.exception(f"从本地数据库查找元数据时出错: {e}")
            # 继续尝试远程读取

    # --- 3. 从远程读取 (Wrapper) ---
    # 总是尝试从远程读取以获取最新内容
    logger.debug(f"尝试通过 Wrapper 从远程读取内容: identifier/permalink='{target_permalink}'")
    try:
        tool_success, tool_content_or_error, tool_metadata_remote = basic_memory.read_note(target_permalink)
    except Exception as e:
        logger.exception(f"调用 basic_memory.read_note 时出错: {e}")
        # 如果本地有元数据，可以考虑返回元数据+错误信息，否则返回失败
        if local_metadata:
            return False, f"知识库工具调用失败: {str(e)}", {**local_metadata, "error": f"Failed to fetch full content: {str(e)}"}
        else:
            return False, f"知识库工具调用失败: {str(e)}", {}

    if not tool_success:
        logger.warning(f"Wrapper (read_note) 读取失败 for '{target_permalink}': {tool_content_or_error}")
        error_msg = f"知识库工具读取失败: {tool_content_or_error}"
        if "not found" in str(tool_content_or_error).lower():
            error_msg = f"笔记未找到: {target_permalink}"
        # 如果本地有元数据，可以考虑返回元数据+错误信息
        if local_metadata:
            return False, error_msg, {**local_metadata, "error": error_msg}
        else:
            return False, error_msg, tool_metadata_remote  # Return tool metadata if any

    # --- 4. 处理远程结果 & (可选) 更新本地缓存 ---
    remote_content = str(tool_content_or_error)  # 实际的完整内容
    final_permalink = tool_metadata_remote.get("permalink", target_permalink)  # 使用权威 permalink
    final_identifier = target_identifier or _get_identifier_from_permalink(final_permalink)

    # 仅当成功获取远程内容和标识符时才更新缓存
    if final_permalink and final_identifier:
        try:
            # 使用远程内容生成新摘要
            remote_title = tool_metadata_remote.get("title")  # 从远程元数据获取标题
            summary = _generate_summary(remote_content, title=remote_title, fallback_text=final_permalink)
            db_file_path = _get_file_path(memory_root, final_identifier)  # 文件路径生成仍使用 memory_root

            # 准备更新本地索引的数据
            db_data_for_update = {
                "title": remote_title or (local_metadata.get("title") if local_metadata else final_identifier.split("/")[-1]),
                "folder": tool_metadata_remote.get("folder")
                or (local_metadata.get("folder") if local_metadata else (final_identifier.split("/")[0] if "/" in final_identifier else "notes")),
                "summary": summary,  # 更新摘要
                "tags": tool_metadata_remote.get("tags") or (local_metadata.get("tags") if local_metadata else None),
                "permalink": final_permalink,
                "file_path": str(db_file_path),
                "sync_status": SyncStatus.SYNCED.name,  # 刚刚同步
                "is_deleted": False,  # 确保未标记为删除
            }

            with session_scope() as session:
                # 查找可能存在的记录（包括已删除的记录）
                existing_item = repo.find_by_permalink(session, final_permalink, include_deleted=True)
                if existing_item:
                    # 如果找到记录（包括可能是已删除的记录），更新它
                    if existing_item.is_deleted:
                        logger.info(f"找到已删除的记录（ID={existing_item.id}），阅读时将其标记为未删除")

                    # 更新所有字段
                    for key, value in db_data_for_update.items():
                        setattr(existing_item, key, value)
                    session.commit()
                else:
                    # 如果没有找到记录，创建新记录
                    repo.create(session, db_data_for_update)

                logger.info(f"已将远程内容摘要更新到本地数据库: permalink='{final_permalink}'")
                # 更新 local_metadata (如果之前获取了) 以反映最新摘要等信息
                if local_metadata:
                    local_metadata.update(
                        {
                            "summary": summary,
                            "title": db_data_for_update["title"],
                            "folder": db_data_for_update["folder"],
                            "tags": db_data_for_update["tags"],
                            "file_path": db_data_for_update["file_path"],
                        }
                    )

        except Exception as e:
            logger.exception(f"更新本地数据库缓存时出错: {e}")
            # 不阻止返回成功获取的内容，但可以在元数据中添加警告
            if local_metadata:
                local_metadata["warning"] = "db_cache_update_failed"
            tool_metadata_remote["warning"] = "db_cache_update_failed"

    # --- 5. 合并元数据和内容返回 ---
    # 优先使用本地获取的元数据（可能已更新），然后是远程工具的元数据
    final_metadata = {
        **(local_metadata or {}),  # Start with local metadata if available
        **tool_metadata_remote,  # Overlay remote metadata (may have more fields)
        "permalink": final_permalink,  # Ensure definitive permalink
        "identifier": final_identifier,  # Ensure definitive identifier
        "source": "remote_content",  # Indicate content source
    }
    # Ensure essential fields are present if possible
    final_metadata.setdefault("title", target_identifier.split("/")[-1] if target_identifier else "Unknown Title")
    final_metadata.setdefault("folder", target_identifier.split("/")[0] if target_identifier and "/" in target_identifier else "notes")

    logger.info(f"从远程成功读取内容: identifier='{final_identifier}', permalink='{final_permalink}'")
    # 返回 成功状态, 完整内容, 合并后的元数据
    return True, remote_content, final_metadata


def execute_delete_note(
    path_or_permalink: str,  # 接受 permalink 或标识符
    repo: MemoryItemRepository,
    basic_memory: BasicMemoryWrapper,
    memory_root: pathlib.Path,
    force: bool = False,  # basic_memory.delete_note 目前忽略 force 参数
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    执行删除笔记的操作 (简化版本):
    1. 接受 path_or_permalink 输入，规范化为 permalink。
    2. 直接调用 BasicMemoryWrapper.delete_note 执行软删除。

    直接传递逻辑到底层实现，保持简洁。
    """
    logger.debug(f"执行删除笔记: input='{path_or_permalink}', force={force}")

    # --- 1. 规范化输入 ---
    target_permalink = path_or_permalink
    if not path_or_permalink.startswith("memory://"):
        target_permalink = f"memory://{path_or_permalink}"
        logger.debug(f"输入被视为标识符，构造的 permalink: {target_permalink}")

    # --- 2. 直接调用 BasicMemoryWrapper ---
    try:
        logger.info(f"直接调用 BasicMemoryWrapper.delete_note 删除: '{target_permalink}'")
        return basic_memory.delete_note(target_permalink)

    except Exception as e:
        logger.exception(f"调用 BasicMemoryWrapper.delete_note 时出错: {e}")
        return False, f"删除笔记时发生内部错误: {str(e)}", {"error": str(e)}
