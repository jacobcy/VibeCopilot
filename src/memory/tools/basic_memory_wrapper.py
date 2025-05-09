#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic Memory 工具封装模块

直接调用 basic-memory CLI 或数据库实现笔记操作。
"""

import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path  # 导入 Path
from typing import Any, Dict, List, Optional, Tuple

# --- 导入配置 ---
from src.core.config import get_config
from src.db.repositories.memory_item_repository import MemoryItemRepository

# --- 重新引入数据库依赖，用于 delete_note ---
from src.db.session_manager import session_scope
from src.models.db.memory_item import MemoryItem

# --- 移除 note_utils 导入 ---
# from src.memory.helpers import note_utils

# --- 移除硬编码的 MEMORY_ROOT_PATH ---
# # 临时硬编码，后续应从配置读取
# MEMORY_ROOT_PATH = os.path.expanduser("~/.cache/basic-memory/vibecopilot") # 示例路径

logger = logging.getLogger(__name__)


class BasicMemoryWrapper:
    """封装 basic-memory CLI 工具调用和数据库操作的类"""

    def __init__(self, project: str = "vibecopilot"):
        self.logger = logging.getLogger(__name__)
        self.project = project
        self.logger.info(f"BasicMemoryWrapper initialized for project '{self.project}'.")
        self._memory_item_repo = MemoryItemRepository()  # 用于 delete_note
        self._project_setup_done = False  # Flag to track if project setup has been done

        # --- 从配置构建 memory_root_path (使用 get_config) ---
        try:
            config_obj = get_config()  # 使用正确的 get_config() 函数

            # 确保我们从正确类型的对象获取配置
            if hasattr(config_obj, "get"):
                try:
                    project_root_str = config_obj.get("paths.project_root")
                    agent_work_dir_str = config_obj.get("paths.agent_work_dir")

                    # 将字符串转换为 Path 对象
                    project_root = Path(project_root_str) if project_root_str else Path.cwd()

                    # 如果 agent_work_dir 是相对路径，则附加到 project_root
                    # 如果是绝对路径，则直接使用
                    agent_work_dir_path = Path(agent_work_dir_str) if agent_work_dir_str else Path(".ai")

                    if agent_work_dir_path.is_absolute():
                        # 已经是绝对路径，直接使用
                        self.memory_root_path = agent_work_dir_path / "memory"
                    else:
                        # 相对路径，附加到 project_root
                        self.memory_root_path = project_root / agent_work_dir_path / "memory"

                    # 确保目录存在
                    self.memory_root_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Memory root path set to: {self.memory_root_path}")

                    # 不在此处调用 setup_project()
                    # self.setup_project()
                except Exception as e:
                    self.logger.exception(f"Error getting memory paths from config: {e}")
                    self.memory_root_path = Path.cwd() / ".ai" / "memory"
                    self.memory_root_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Using default memory path: {self.memory_root_path}")

                    # 不在此处调用 setup_project()
                    # self.setup_project()
        except Exception as e:
            self.logger.error(f"Failed to determine memory root path from config: {e}. Using default relative path.")
            # 提供一个备用路径
            self.memory_root_path = Path(".ai/memory")  # 简单的相对路径作为后备
            self.memory_root_path.mkdir(parents=True, exist_ok=True)

            # 不在此处调用 setup_project()
            # self.setup_project()

    def _ensure_project_is_ready(self) -> bool:
        """Ensures the basic-memory project is set up. Call this before CLI operations."""
        if not self._project_setup_done:
            if self.setup_project():
                self._project_setup_done = True
            else:
                # Log an error but don't necessarily stop if setup_project handles its own errors
                self.logger.error("Failed to set up basic-memory project during _ensure_project_is_ready.")
                return False  # Indicate failure to set up
        return self._project_setup_done

    def setup_project(self) -> bool:
        """设置basic-memory项目，确保项目路径正确"""
        try:
            # 首先检查项目是否已存在
            check_cmd = ["basic-memory", "project", "list"]
            process = subprocess.run(check_cmd, capture_output=True, text=True)

            # 如果项目已存在，检查路径是否正确
            if self.project in process.stdout:
                self.logger.info(f"项目 '{self.project}' 已存在于basic-memory中")

                # 检查当前项目
                current_cmd = ["basic-memory", "project", "current"]
                process = subprocess.run(current_cmd, capture_output=True, text=True)

                # 如果不是当前项目，设为当前项目
                if self.project not in process.stdout:
                    default_cmd = ["basic-memory", "project", "default", self.project]
                    process = subprocess.run(default_cmd, capture_output=True, text=True)
                    if process.returncode == 0:
                        self.logger.info(f"已将 '{self.project}' 设为当前项目")
                    else:
                        self.logger.error(f"设置当前项目失败: {process.stderr}")
                        return False

                return True

            # 项目不存在，创建新项目
            path_str = str(self.memory_root_path)
            add_cmd = ["basic-memory", "project", "add", self.project, path_str]
            process = subprocess.run(add_cmd, capture_output=True, text=True)

            if process.returncode == 0:
                self.logger.info(f"成功创建项目 '{self.project}' 指向路径 {path_str}")

                # 设为当前项目
                default_cmd = ["basic-memory", "project", "default", self.project]
                process = subprocess.run(default_cmd, capture_output=True, text=True)

                if process.returncode == 0:
                    self.logger.info(f"已将 '{self.project}' 设为当前项目")
                    return True
                else:
                    self.logger.error(f"设置当前项目失败: {process.stderr}")
                    return False
            else:
                self.logger.error(f"创建项目失败: {process.stderr}")
                return False

        except Exception as e:
            self.logger.exception(f"设置basic-memory项目时出错: {e}")
            return False

    def _run_cli_command(self, command: List[str], input_data: Optional[str] = None) -> Tuple[bool, str, str]:
        """执行 basic-memory CLI 命令的辅助函数"""
        if not self._ensure_project_is_ready():
            # If project setup failed, we cannot run CLI commands reliably.
            # The error would have been logged by _ensure_project_is_ready or setup_project.
            return False, "", "basic-memory project setup failed or not ready."

        full_cmd = ["basic-memory"]
        if self.project:
            full_cmd.extend([f"--project={self.project}"])
        full_cmd.extend(command)

        self.logger.debug(f"Executing CLI command: {' '.join(full_cmd)}")
        try:
            process = subprocess.Popen(
                full_cmd,
                stdin=subprocess.PIPE if input_data is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            stdout, stderr = process.communicate(input=input_data)

            if process.returncode == 0:
                self.logger.debug(f"CLI command successful. stdout:\n{stdout}")
                return True, stdout.strip(), stderr.strip()
            else:
                error_msg = stderr.strip() or stdout.strip() or f"CLI command failed with return code {process.returncode}"
                self.logger.error(f"CLI command failed: {error_msg}")
                return False, stdout.strip(), error_msg  # 返回 stdout 和 stderr
        except FileNotFoundError:
            self.logger.exception("'basic-memory' command not found. Is it installed and in PATH?")
            return False, "", "'basic-memory' command not found."
        except Exception as e:
            self.logger.exception(f"Error executing CLI command: {e}")
            return False, "", f"Error executing CLI command: {str(e)}"

    def write_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """调用 basic-memory tool write-note 创建或更新笔记"""
        self.logger.debug(f"Wrapper: Calling CLI write-note for '{folder}/{title}'")
        command = ["tool", "write-note", "--title", title, "--folder", folder]
        if tags:
            command.extend(["--tags", tags])

        # 预处理内容，确保换行符正确
        processed_content = content.replace("\\n", "\n")

        success, stdout, stderr = self._run_cli_command(command, input_data=processed_content)

        if not success:
            # 如果错误信息是 "already exists"，我们可能需要更新？
            # Basic Memory CLI 的 write-note 默认行为是覆盖，所以这里直接报告失败
            error_message = f"Failed to write note: {stderr or stdout}"
            self.logger.error(error_message)
            return False, error_message, {"error": stderr or stdout}

        # 解析 Basic Memory 返回的 Markdown 格式输出
        self.logger.info(f"CLI write-note successful. Output:\n{stdout}")
        result_data = {"title": title, "folder": folder, "tags": tags.split(",") if tags else []}
        permalink = ""
        checksum = ""

        # 提取 permalink
        permalink_match = re.search(r"permalink:\s*([^\n]+)", stdout)
        if permalink_match:
            permalink = permalink_match.group(1).strip()
            if not permalink.startswith("memory://"):
                permalink = f"memory://{permalink}"  # 确保格式正确
            result_data["permalink"] = permalink
            self.logger.info(f"Extracted permalink: {permalink}")

        # 提取 checksum
        checksum_match = re.search(r"checksum:\s*([^\n]+)", stdout)
        if checksum_match:
            checksum = checksum_match.group(1).strip()
            result_data["checksum"] = checksum
            self.logger.info(f"Extracted checksum: {checksum}")

        # 构建成功消息 (简化)
        tags_display = tags or "无"
        word_count = len(processed_content.split())
        success_message = f"📝 内容已保存! Permalink: {permalink or 'N/A'}, 标签: {tags_display}, 字数: {word_count}"

        return True, success_message, result_data

    def read_note(self, identifier: str) -> Tuple[bool, str, Dict[str, Any]]:
        """调用 basic-memory tool read-note 读取笔记"""
        self.logger.debug(f"Wrapper: Calling CLI read-note for '{identifier}'")

        # 预处理标识符，移除可能的 memory:// 前缀
        clean_identifier = identifier
        if identifier.startswith("memory://"):
            clean_identifier = identifier[9:]
            self.logger.debug(f"Removed memory:// prefix, using: {clean_identifier}")

        command = ["tool", "read-note", clean_identifier]
        success, stdout, stderr = self._run_cli_command(command)

        if not success:
            error_message = f"Failed to read note: {stderr or stdout}"
            self.logger.warning(error_message)
            # 检查是否是 Not Found 错误
            if "Note Not Found" in stderr or "not found" in stderr.lower() or "Note Not Found" in stdout or "not found" in stdout.lower():
                return False, f"Note Not Found: {identifier}", {"error": stderr or stdout}
            return False, error_message, {"error": stderr or stdout}

        # 尝试解析元数据（如果 read-note 输出包含）
        metadata = {"identifier": identifier}
        title = os.path.basename(clean_identifier)  # 默认标题
        permalink = identifier  # 默认 permalink

        # 简单提取标题 (假设 # 开头)
        title_match = re.search(r"^#\s+(.+)", stdout, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            metadata["title"] = title

        # 提取 permalink (假设在输出中)
        permalink_match = re.search(r"permalink:\s*([^\n]+)", stdout)
        if permalink_match:
            extracted_permalink = permalink_match.group(1).strip()
            if not extracted_permalink.startswith("memory://"):
                permalink = f"memory://{extracted_permalink}"
            else:
                permalink = extracted_permalink
            metadata["permalink"] = permalink

        # 提取 tags (假设 ## Tags 结构)
        tags_section = re.search(r"## Tags\s*([\s\S]*?)(?:##|$)", stdout)
        if tags_section:
            tags_content = tags_section.group(1).strip()
            tags_list = [tag.strip("- \n") for tag in tags_content.split("\n") if tag.strip().startswith("-")]
            metadata["tags"] = tags_list

        # content 就是 stdout 本身
        content = stdout
        self.logger.info(f"CLI read-note successful for '{identifier}'")
        return True, content, metadata

    def delete_note(self, identifier: str) -> Tuple[bool, str, Dict[str, Any]]:
        """软删除数据库中的笔记记录，并尝试删除本地文件"""
        self.logger.debug(f"Wrapper: Soft deleting note '{identifier}' in DB and attempting file deletion.")

        # 规范化 permalink
        permalink = identifier
        if not permalink.startswith("memory://"):
            permalink = f"memory://{identifier}"

        try:
            with session_scope() as session:
                item = self._memory_item_repo.find_by_permalink(session, permalink)
                if not item:
                    # 如果数据库记录不存在，认为删除（软删除目标）成功
                    self.logger.warning(f"Note with permalink '{permalink}' not found in DB. Treating as deleted.")
                    # 尝试使用规范化的 permalink 直接删除文件 (即使数据库中无记录)
                    # 提取干净的 identifier
                    clean_identifier = permalink[9:] if permalink.startswith("memory://") else permalink
                    file_path = self._attempt_delete_local_file(clean_identifier)
                    return True, f"Note '{identifier}' not found, but deleting any associated file.", {"status": "not_found"}

                # 检查是否已经标记为删除
                if item.is_deleted:
                    self.logger.info(f"Note with permalink '{permalink}' already marked as deleted.")
                    return True, f"Note '{identifier}' already deleted.", {"status": "already_deleted"}

                # 执行软删除 (更新 is_deleted 字段)
                try:
                    # 修改: 使用 is_deleted 字段代替 deleted_at
                    item.is_deleted = True
                    item.updated_at = datetime.now(timezone.utc)
                    session.commit()
                    self.logger.info(f"Soft deleted item in DB: {permalink}")

                    # 尝试删除关联的本地文件
                    file_path = self._attempt_delete_local_file(item)
                    if file_path:
                        self.logger.info(f"删除关联文件成功: {file_path}")
                        return True, f"笔记 '{identifier}' 已软删除，本地文件已删除。", {"status": "deleted", "file_deleted": True}
                    else:
                        self.logger.info(f"笔记 '{identifier}' 已软删除，无本地文件或删除失败。")
                        return True, f"笔记 '{identifier}' 已软删除，无本地文件或删除失败。", {"status": "deleted", "file_deleted": False}
                except Exception as e:
                    self.logger.exception(f"Error during soft delete for '{permalink}': {e}")
                    return False, f"DB error during soft delete: {str(e)}", {"status": "error", "error": str(e)}

        except Exception as e:
            self.logger.exception(f"Error during soft delete for '{permalink}': {e}")
            return False, f"DB error during soft delete: {str(e)}", {"status": "error", "error": str(e)}

    def _attempt_delete_local_file(self, item_or_identifier) -> Optional[str]:
        """
        尝试删除与 MemoryItem 或标识符关联的本地文件

        Args:
            item_or_identifier: MemoryItem 对象或字符串标识符

        Returns:
            Optional[str]: 如果成功删除则返回文件路径，否则返回 None
        """
        try:
            # 确定 identifier
            if isinstance(item_or_identifier, str):
                # 输入是字符串标识符
                identifier = item_or_identifier
                if identifier.startswith("memory://"):
                    identifier = identifier[9:]
            else:
                # 输入是 MemoryItem 对象
                item = item_or_identifier
                if not item.permalink:
                    self.logger.warning(f"Item ID {item.id} has no permalink, cannot determine file path.")
                    return None

                # 从 permalink 获取标识符
                identifier = item.permalink
                if identifier.startswith("memory://"):
                    identifier = identifier[9:]

            # 检查标识符是否有效
            if not identifier or ".." in identifier or identifier.startswith("/"):  # 基础安全检查
                self.logger.error(f"Invalid identifier: '{identifier}'. Aborting file deletion.")
                return None

            # 构建文件路径: memory_root_path/identifier.md
            relative_path = f"{identifier}.md"
            file_path = self.memory_root_path / relative_path

            # 尝试删除文件
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.logger.info(f"成功删除文件: {file_path}")
                    return str(file_path)
                except Exception as del_error:
                    self.logger.error(f"删除文件失败 '{file_path}': {del_error}")
                    return None
            else:
                self.logger.info(f"文件不存在，无需删除: {file_path}")
                return None
        except Exception as e:
            self.logger.exception(f"文件删除过程出错: {e}")
            return None

    def search_notes(self, query: str, types: Optional[List[str]] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """调用 basic-memory tool search-notes 搜索笔记"""
        self.logger.debug(f"Wrapper: Calling CLI search-notes with query '{query}', types: {types}")
        command = ["tool", "search-notes", query]
        # basic-memory CLI 当前可能不支持 --types
        # if types:
        #     command.extend(["--types", ",".join(types)])

        success, stdout, stderr = self._run_cli_command(command)

        if not success:
            error_message = f"Failed to search notes: {stderr or stdout}"
            self.logger.error(error_message)
            return False, error_message, []

        self.logger.info(f"CLI search-notes successful. Output:\n{stdout}")
        results_list = []
        message = "Search completed."

        # 尝试解析为 JSON
        try:
            results_list = json.loads(stdout)
            if isinstance(results_list, list):
                message = f"Found {len(results_list)} results (JSON)."
                self.logger.info(message)
            else:
                message = "Search result is not a JSON list."
                self.logger.warning(f"{message} Output type: {type(results_list)}")
                results_list = [results_list]  # 尝试包装
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试按行处理 (假设是 Markdown 或简单文本列表)
            self.logger.warning("Search output is not JSON, attempting line-based parsing.")
            lines = stdout.strip().split("\n")
            # 简单的处理：将每行视为一个结果项
            # TODO: 可能需要更复杂的解析来提取 permalink, title 等
            results_list = [{"raw_output": line} for line in lines if line.strip()]
            message = f"Found {len(results_list)} results (parsed as lines)."
            self.logger.info(message)

        return True, message, results_list


# --- 移除所有占位符函数 ---
