#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存操作服务模块

处理与 MemoryItem 相关的业务逻辑，如 CRUD、导入、路径解析、摘要生成。
协调 BasicMemoryWrapper 和 MemoryItemRepository。
"""

import logging
import os
import pathlib
from datetime import datetime, timezone  # Import datetime and timezone
from typing import Any, Dict, List, Optional, Tuple

# --- 依赖项 ---
from sqlalchemy import desc  # Import desc for ordering

from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.db.session_manager import session_scope

# 实际的文件系统包装器 - 不再是 TODO
from src.memory.services.memory_crud import execute_create_note, execute_delete_note, execute_read_note
from src.memory.tools.basic_memory_wrapper import BasicMemoryWrapper
from src.memory.tools.filesystem_wrapper import TODO_FilesystemWrapper as FilesystemWrapper
from src.models.db.memory_item import MemoryItem  # Import Model for ordering/typing
from src.parsing.processors.document_processor import DocumentProcessor

# SyncStatus enum can be used here in the service layer
from src.status.enums import SyncStatus

logger = logging.getLogger(__name__)
doc_processor = DocumentProcessor()  # Initialize processor once for reuse

# ===== 路径与标识符处理 (服务层逻辑) =====


def _get_or_derive_identifier(folder: Optional[str], title: Optional[str], permalink: Optional[str]) -> Optional[str]:
    """尝试获取或派生规范化的 identifier"""
    if folder and title:
        folder = folder.strip("/")
        title = title.strip()
        return f"{folder}/{title}" if folder else title
    if permalink:
        return _get_identifier_from_permalink(permalink)
    logger.warning("无法确定 identifier，缺少 folder/title 和有效的 permalink")
    return None


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


# ===== 导入操作 (服务层逻辑) =====


def execute_import_documents(
    source_path: str,
    repo: MemoryItemRepository,
    basic_memory: BasicMemoryWrapper,
    # filesystem: TODO_FilesystemWrapper, # Remove TODO_
    filesystem: FilesystemWrapper,  # Use the imported FilesystemWrapper
    memory_root: pathlib.Path,
    recursive: bool = False,
    target_folder_prefix: str = "",  # 默认不添加前缀
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    执行从文件系统导入文档的操作:
    1. 判断源路径是文件还是目录。
    2. 如果是文件，直接处理该文件；如果是目录，列出所有文件。
    3. 对每个文件:
        a. 读取内容。
        b. 调用 Wrapper 创建远程笔记。
        c. 生成摘要。
        d. 调用 Repository 创建/更新本地索引。
    """
    logger.info(f"执行导入: source='{source_path}', recursive={recursive}, prefix='{target_folder_prefix}'")
    source_path_abs = os.path.abspath(os.path.expanduser(source_path))

    # 检查源路径是否存在
    if not os.path.exists(source_path_abs):
        return False, f"源路径不存在: {source_path_abs}", {}

    imported_count, failed_count, db_synced_count = 0, 0, 0
    db_errors, processed_files = [], []
    file_paths = []

    try:
        # --- 1. 检查路径类型并获取文件列表 ---
        if os.path.isfile(source_path_abs):
            # 单个文件导入
            logger.info(f"源路径是单个文件: {source_path_abs}")
            if source_path_abs.lower().endswith(".md"):
                file_paths = [source_path_abs]
            else:
                return False, f"不支持的文件类型: {source_path_abs}，只支持导入Markdown文件(.md)", {}
        elif os.path.isdir(source_path_abs):
            # 目录导入
            logger.info(f"源路径是目录: {source_path_abs}")
            list_success, list_msg, dir_file_paths = filesystem.list_directory(source_path_abs, recursive=recursive)

            if not list_success:
                logger.error(f"无法列出源目录 '{source_path_abs}': {list_msg}")
                return False, f"无法列出源目录内容: {list_msg}", {}

            file_paths = dir_file_paths
        else:
            return False, f"无效的路径类型: {source_path_abs}", {}

        # 检查是否找到文件
        if not file_paths:
            return True, "源路径下未找到可导入的 Markdown 文件 (.md)。", {"imported": 0, "failed": 0, "db_synced": 0}

        logger.info(f"找到 {len(file_paths)} 个潜在文件进行导入...")

        # --- 2. Process each file ---
        for file_path in file_paths:
            # Basic check if it's an md file before processing
            if not file_path.lower().endswith(".md"):
                logger.debug(f"跳过非 Markdown 文件: {file_path}")
                continue

            processed_files.append(file_path)
            base_name = os.path.basename(file_path)
            try:
                logger.debug(f"处理文件: {file_path}")
                # a. Read content using FilesystemWrapper
                read_success, read_msg_or_content, content = filesystem.read_file(file_path)  # 直接获取content

                if not read_success:
                    logger.error(f"读取文件失败 '{base_name}': {read_msg_or_content}")
                    failed_count += 1
                    continue

                # 确保content是字符串
                if not content:
                    content = str(read_msg_or_content)  # 如果第三个参数为空则使用第二个参数
                else:
                    content = str(content)

                # Determine title and target folder (logic remains the same)
                title = base_name
                if title.lower().endswith(".md"):
                    title = title[:-3]

                # 计算相对路径和目标文件夹
                source_dir = os.path.dirname(source_path_abs) if os.path.isfile(source_path_abs) else source_path_abs
                relative_path = os.path.relpath(file_path, start=source_dir)
                folder_parts = os.path.dirname(relative_path).split(os.sep)
                base_folder = "/".join(part for part in folder_parts if part and part != ".")

                # 构建最终的目标文件夹
                # 只有当 target_folder_prefix 非空且 base_folder 非空时才用斜杠连接
                if target_folder_prefix and base_folder:
                    target_folder = f"{target_folder_prefix}/{base_folder}"
                elif target_folder_prefix:
                    target_folder = target_folder_prefix
                elif base_folder:
                    target_folder = base_folder
                else:
                    target_folder = "notes"  # 默认文件夹

                target_folder = target_folder.strip("/")
                logger.debug(f"准备写入笔记: title='{title}', folder='{target_folder}'")

                # b. Call Wrapper to create remote note (logic remains the same)
                try:
                    write_success, write_msg, write_data = basic_memory.write_note(content, title, target_folder)
                except Exception as wrapper_err:
                    logger.exception(f"调用 basic_memory.write_note 导入 '{base_name}' 时出错: {wrapper_err}")
                    failed_count += 1
                    continue

                if not write_success:
                    logger.error(f"导入文件 '{base_name}' 到知识库失败: {write_msg}")
                    failed_count += 1
                    continue

                imported_count += 1
                # 获取 basic-memory 返回的 permalink
                permalink = write_data.get("permalink")
                if not permalink:
                    logger.warning(f"导入 '{base_name}' 成功但未获取 Permalink，无法同步DB。")
                    continue

                # c. 生成摘要
                summary = _generate_summary(content, title=title, fallback_text=permalink)

                # d. 同步数据库 - 处理可能存在的软删除情况
                try:
                    # 获取标识符用于构建文件路径
                    identifier = _get_identifier_from_permalink(permalink)
                    if not identifier:
                        raise ValueError(f"无法从 permalink '{permalink}' 获取有效标识符")

                    db_file_path = _get_file_path(memory_root, identifier)

                    db_data = {
                        "title": title,
                        "folder": target_folder,
                        "summary": summary,
                        "permalink": permalink,  # 使用 basic-memory 返回的 permalink
                        "file_path": str(db_file_path),
                        "sync_status": SyncStatus.SYNCED.name,
                        "is_deleted": False,  # 重新导入时确保记录为未删除状态
                    }

                    with session_scope() as session:
                        # 查找可能存在的记录（包括已删除的记录）
                        existing_item = repo.find_by_permalink(session, permalink, include_deleted=True)
                        if existing_item:
                            # 如果找到记录，更新它
                            logger.info(f"找到现有记录（ID={existing_item.id}，已删除={existing_item.is_deleted}），进行更新")
                            for key, value in db_data.items():
                                setattr(existing_item, key, value)
                            session.commit()
                            db_synced_count += 1
                        else:
                            # 如果没有找到记录，创建新记录
                            repo.create(session, db_data)
                            db_synced_count += 1

                    logger.info(f"文件 '{base_name}' 导入并同步DB成功. Permalink: {permalink}")
                except Exception as db_err:
                    logger.error(f"同步导入记录DB失败 (permalink={permalink}, file={base_name}): {db_err}")
                    db_errors.append(base_name)
            except Exception as file_proc_err:
                logger.exception(f"处理文件 '{file_path}' 时意外错误: {file_proc_err}")
                failed_count += 1
    except Exception as import_err:
        logger.exception(f"导入文档过程意外错误: {import_err}")
        return False, f"导入过程错误: {str(import_err)}", {}

    # --- Format final message (logic remains the same) ---
    final_message = f"文档导入完成。处理文件数: {len(processed_files)}。"
    final_message += f" 成功导入远程: {imported_count} 个, 读取/处理失败: {failed_count} 个。"
    if db_synced_count > 0:
        final_message += f" 本地索引同步成功: {db_synced_count} 条。"
    if db_errors:
        final_message += f" 本地索引同步失败: {len(db_errors)} 条 ({', '.join(db_errors[:3])}{'...' if len(db_errors)>3 else ''})"
    logger.info(final_message)
    final_data = {
        "processed": len(processed_files),
        "imported_remote": imported_count,
        "failed_local": failed_count,
        "db_synced": db_synced_count,
        "db_errors": len(db_errors),
    }
    overall_success = imported_count > 0 or (failed_count == 0 and not db_errors)
    return overall_success, final_message.strip(), final_data


# ===== 查询操作 (服务层逻辑) =====


def execute_list_notes(
    repo: MemoryItemRepository, folder: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 100
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    列出笔记 (从 DB 查询索引)
    """
    logger.debug(f"执行列出笔记: folder='{folder or 'all'}', tags='{tags or 'any'}', limit={limit}")

    try:
        with session_scope() as session:
            # Use the generic find_items method
            items = repo.find_items(
                session, folder=folder, tags=tags, include_deleted=False, limit=limit, order_by=desc(MemoryItem.updated_at)  # Order by most recent
            )

            if not items:
                # Construct a more informative message
                filter_desc = []
                if folder:
                    filter_desc.append(f"文件夹 '{folder}'")
                if tags:
                    filter_desc.append(f"标签 {tags}")
                message = f"未找到{('在' + ' 且 '.join(filter_desc)) if filter_desc else ''} 任何笔记。"
                return True, message, []

            # Format the list for output
            formatted_list = []
            for item in items:
                formatted_list.append(
                    {
                        "id": item.id,
                        "title": item.title,
                        "folder": item.folder,
                        "permalink": item.permalink,
                        "summary": item.summary,  # Use the stored summary
                        "tags": item.tags,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    }
                )

            # Prepare a simple string message for console display maybe?
            # This part might be better handled by the CLI layer itself based on the returned data
            message_lines = [f"找到 {len(items)} 个笔记{' (最多显示 ' + str(limit) + ' 个)' if len(items) == limit else ''}:"]
            for idx, item_data in enumerate(formatted_list, 1):
                title = item_data["title"]
                folder = item_data["folder"] or "默认"
                permalink = item_data["permalink"] or ""
                # 提取标识符（去除 memory:// 前缀）
                identifier = permalink[9:] if permalink.startswith("memory://") else permalink
                summary = item_data["summary"] or "无摘要"
                tags_str = f' [Tags: {item_data["tags"]}]' if item_data["tags"] else ""

                # 新的格式：显示标识符、标题和文件夹
                message_lines.append(f"======\n{idx}. 标识符: {identifier}\n   标题: {title}\n   文件夹: {folder}{tags_str}\n---\n{summary}")

            message = "\n".join(message_lines)
            return True, message, formatted_list
    except Exception as e:
        logger.exception(f"列出笔记时发生错误: {e}")
        return False, f"列出笔记时发生错误: {str(e)}", []


# TODO: Add execute_search_notes leveraging repo.search_summary_title_tags
# TODO: Add functions for statistics if needed, using repo.count_items, repo.list_folders etc.


def _get_identifier_from_permalink(permalink: Optional[str]) -> Optional[str]:
    """从 permalink 提取标识符（去掉前缀）"""
    if not permalink:
        return None
    prefix = "memory://"
    if permalink.startswith(prefix):
        return permalink[len(prefix) :]
    return permalink  # 如果没有前缀，直接返回
