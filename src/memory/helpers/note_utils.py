#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记工具模块

提供对Basic Memory笔记的操作功能，简化服务中的笔记处理逻辑。
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def create_note(content: str, title: str, folder: str, tags: Optional[str] = None, project: str = "vibecopilot") -> Tuple[bool, str, Dict[str, Any]]:
    """
    创建新笔记

    Args:
        content: 笔记内容
        title: 笔记标题
        folder: 存储目录
        tags: 标签列表（逗号分隔）
        project: 项目名称

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    try:
        logger.info(f"创建笔记: {title} 到 {folder}")

        # 预处理内容，确保换行符被正确处理
        processed_content = content
        if "\\n" in content:
            processed_content = content.replace("\\n", "\n")

        # 简化文件夹名称，避免嵌套路径
        if "/" in folder:
            folder = folder.split("/")[0]

        # 构建命令
        cmd = ["basic-memory"]
        if project:
            cmd.extend([f"--project={project}"])

        cmd.extend(["tool", "write-note", "--title", title, "--folder", folder])

        if tags:
            cmd.extend(["--tags", tags])

        # 执行命令
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 发送内容
        stdout, stderr = process.communicate(input=processed_content)

        if process.returncode != 0:
            error_msg = stderr.strip() or "创建笔记失败"
            return False, f"保存内容失败: {error_msg}", {}

        try:
            # 解析结果
            result = json.loads(stdout)
        except json.JSONDecodeError:
            # 解析失败时创建默认结果
            result = {
                "permalink": f"memory://{folder}/{title.replace(' ', '_').lower()}.md",
                "title": title,
                "folder": folder,
                "tags": tags.split(",") if tags else [],
            }

        # 计算字数
        word_count = len(processed_content.split())

        success_message = f"📝 内容已保存!\n存储位置: {folder}/{title}.md\n标签: {tags or '无'}\n字数: {word_count}字"

        return True, success_message, result

    except Exception as e:
        error_message = f"保存内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def read_note(path: str, project: str = "vibecopilot") -> Tuple[bool, str, Dict[str, Any]]:
    """
    读取笔记内容

    Args:
        path: 笔记路径或标识符
        project: 项目名称

    Returns:
        元组，包含(是否成功, 内容, 元数据)
    """
    try:
        logger.info(f"读取笔记: {path}")

        # 尝试不同的路径变体
        possible_paths = _generate_path_variants(path)
        logger.info(f"将尝试以下路径: {possible_paths}")

        for try_path in possible_paths:
            # 尝试不同命令形式
            commands_to_try = [
                ["basic-memory", "tool", "read-note", try_path],
                ["basic-memory", f"--project={project}", "tool", "read-note", try_path],
            ]

            for cmd in commands_to_try:
                logger.info(f"尝试命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                if result.returncode == 0:
                    logger.info(f"成功读取路径: {try_path}")
                    try:
                        # 解析输出
                        output_data = json.loads(result.stdout)

                        if not output_data or "content" not in output_data:
                            continue

                        # 处理内容中的换行符
                        if isinstance(output_data["content"], str):
                            output_data["content"] = output_data["content"].replace("\\n", "\n")

                        return True, output_data["content"], output_data
                    except json.JSONDecodeError:
                        # 解析失败时直接返回内容
                        return True, result.stdout, {"content": result.stdout, "title": path}

        # 所有尝试失败
        return False, f"无法找到文档: {path}", {}

    except Exception as e:
        error_message = f"读取内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def update_note(path: str, content: str, tags: Optional[str] = None, project: str = "vibecopilot") -> Tuple[bool, str, Dict[str, Any]]:
    """
    更新笔记内容

    Args:
        path: 笔记路径或标识符
        content: 更新后的内容
        tags: 更新的标签（逗号分隔）
        project: 项目名称

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    try:
        logger.info(f"更新笔记: {path}")

        # 首先读取现有内容
        success, _, existing_data = read_note(path, project)
        if not success:
            return False, f"无法找到要更新的文档: {path}", {}

        # 获取标题和文件夹信息
        title = existing_data.get("title", os.path.basename(path))
        folder = _extract_folder(path, existing_data)

        logger.info(f"更新文档: 标题={title}, 文件夹={folder}")

        # 调用创建函数来更新笔记
        return create_note(content, title, folder, tags, project)

    except Exception as e:
        error_message = f"更新内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def delete_note(path: str, memory_root: str, force: bool = False, project: str = "vibecopilot") -> Tuple[bool, str, Dict[str, Any]]:
    """
    删除笔记

    Args:
        path: 笔记路径或标识符
        memory_root: 记忆根目录
        force: 是否强制删除
        project: 项目名称

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    try:
        logger.info(f"删除笔记: {path}, 强制: {force}")

        # 如果不是强制删除，首先检查文档是否存在
        if not force:
            success, _, _ = read_note(path, project)
            if not success:
                return False, f"无法找到要删除的文档: {path}", {}

        # 收集所有可能的文件路径
        search_identifier = path.split("/")[-1]
        logger.info(f"使用标识符搜索笔记: {search_identifier}")

        # 由于依赖关系的复杂性，这里我们直接尝试从memory_root构建路径
        possible_paths = _collect_delete_paths(path, [], memory_root)
        logger.info(f"尝试删除以下路径: {possible_paths}")

        # 尝试删除文件
        deleted = False
        deleted_paths = []

        for file_path in possible_paths:
            if os.path.exists(file_path):
                try:
                    logger.info(f"删除文件: {file_path}")
                    os.remove(file_path)
                    deleted = True
                    deleted_paths.append(file_path)
                except Exception as e:
                    logger.error(f"删除文件 {file_path} 失败: {str(e)}")

        # 清理索引
        identifiers_to_clean = _collect_index_identifiers(path, [])
        logger.info(f"尝试清理以下标识符的索引: {identifiers_to_clean}")

        # 清理索引
        for identifier in identifiers_to_clean:
            try:
                commands = [
                    ["basic-memory", "tool", "delete-note", identifier],
                    ["basic-memory", f"--project={project}", "tool", "delete-note", identifier],
                ]

                for cmd in commands:
                    logger.info(f"执行索引清理命令: {' '.join(cmd)}")
                    subprocess.run(cmd, capture_output=True, text=True, check=False)
            except Exception as e:
                logger.warning(f"清理标识符 {identifier} 的索引失败: {str(e)}")

        # 处理删除结果
        if not deleted and force:
            return True, f"🗑️ 已删除文档（文件不存在）: {path}", {"permalink": path, "status": "not_found_but_ok"}

        if not deleted:
            return False, f"无法删除文档: {path}，未找到对应文件", {}

        success_message = f"🗑️ 已删除文档: {path} (删除了{len(deleted_paths)}个文件)"
        if len(deleted_paths) > 0:
            success_message += f"\n删除的文件: {', '.join(os.path.basename(p) for p in deleted_paths)}"

        return True, success_message, {"permalink": path, "deleted_files": deleted_paths, "status": "deleted"}

    except Exception as e:
        error_message = f"删除内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


# 辅助函数
def _generate_path_variants(path: str) -> List[str]:
    """生成路径的各种变体以提高查找成功率"""
    possible_paths = [path]

    # 连字符与下划线变体
    if "_" in path:
        possible_paths.append(path.replace("_", "-"))
    if "-" in path:
        possible_paths.append(path.replace("-", "_"))

    # 处理带路径分隔符的情况
    if "/" in path:
        folder, filename = os.path.split(path)

        # 添加文件夹使用连字符的变体
        possible_paths.append(f"{folder.replace('_', '-')}/{filename}")

        # 添加文件名使用连字符的变体
        possible_paths.append(f"{folder}/{filename.replace('_', '-')}")

        # 添加文件夹和文件名都使用连字符的变体
        possible_paths.append(f"{folder.replace('_', '-')}/{filename.replace('_', '-')}")

        # 处理可能的嵌套路径问题
        if folder.endswith(folder.split("/")[-1]):
            # 如果文件夹名重复，尝试使用非重复版本
            non_nested_folder = folder.split("/")[0]
            possible_paths.append(f"{non_nested_folder}/{filename}")
            possible_paths.append(f"{non_nested_folder}/{filename.replace('_', '-')}")
            possible_paths.append(f"{non_nested_folder.replace('_', '-')}/{filename.replace('_', '-')}")

        # 尝试只使用文件名部分
        possible_paths.append(filename)
        possible_paths.append(filename.replace("_", "-"))

    return possible_paths


def _extract_folder(path: str, existing_data: Dict[str, Any]) -> str:
    """从路径和现有数据中提取文件夹名称"""
    # 从path提取文件夹部分
    path_folder = ""
    if "/" in path:
        path_folder = path.split("/")[0]

    # 从existing_data中提取文件夹信息
    existing_folder = existing_data.get("folder", "")
    if existing_folder and isinstance(existing_folder, str):
        # 清理可能的路径前缀
        if existing_folder.startswith("memory://"):
            existing_folder = existing_folder[9:]

        # 只取文件夹的第一部分，避免嵌套
        if "/" in existing_folder:
            existing_folder = existing_folder.split("/")[0]

    # 选择合适的文件夹名
    if existing_folder and existing_folder != path_folder:
        # 如果两者不同，且existing_folder非空，优先使用existing_folder
        return existing_folder
    elif path_folder:
        # 否则使用从path提取的文件夹（如果有）
        return path_folder
    else:
        # 如果都没有，使用默认值
        return "notes"


def _collect_delete_paths(path: str, search_results: List[Dict[str, Any]], memory_root: str) -> List[str]:
    """收集所有可能需要删除的文件路径"""
    possible_paths = []

    # 1. 从搜索结果中提取路径
    if search_results:
        for item in search_results:
            permalink = item.get("permalink", "")
            title = item.get("title", "")

            if permalink:
                # 直接使用permalink构建文件路径
                possible_paths.append(os.path.join(memory_root, permalink + ".md"))

                # 替换连字符为下划线的变体
                if "-" in permalink:
                    possible_paths.append(os.path.join(memory_root, permalink.replace("-", "_") + ".md"))

            # 如果title匹配，尝试使用title
            search_identifier = path.split("/")[-1]
            if title and search_identifier in title:
                possible_paths.append(os.path.join(memory_root, title + ".md"))
                possible_paths.append(os.path.join(memory_root, title.replace(" ", "_") + ".md"))
                possible_paths.append(os.path.join(memory_root, title.replace(" ", "-") + ".md"))

    # 2. 基于原始路径构建更多变体
    # 主路径变体
    possible_paths.append(os.path.join(memory_root, path + ".md"))

    # 替换下划线为连字符
    if "_" in path:
        possible_paths.append(os.path.join(memory_root, path.replace("_", "-") + ".md"))

    # 替换连字符为下划线
    if "-" in path:
        possible_paths.append(os.path.join(memory_root, path.replace("-", "_") + ".md"))

    # 3. 处理可能的嵌套情况
    if "/" in path:
        folder, filename = path.split("/", 1)

        # 基本嵌套路径
        possible_paths.append(os.path.join(memory_root, folder, filename + ".md"))
        possible_paths.append(os.path.join(memory_root, folder.replace("_", "-"), filename + ".md"))
        possible_paths.append(os.path.join(memory_root, folder, filename.replace("_", "-") + ".md"))
        possible_paths.append(os.path.join(memory_root, folder.replace("_", "-"), filename.replace("_", "-") + ".md"))

        # 双重嵌套路径
        possible_paths.append(os.path.join(memory_root, folder, folder, filename + ".md"))
        possible_paths.append(os.path.join(memory_root, folder.replace("_", "-"), folder.replace("_", "-"), filename + ".md"))
        possible_paths.append(os.path.join(memory_root, folder, folder, filename.replace("_", "-") + ".md"))
        possible_paths.append(os.path.join(memory_root, folder.replace("_", "-"), folder.replace("_", "-"), filename.replace("_", "-") + ".md"))

        # 只使用文件名部分的变体
        possible_paths.append(os.path.join(memory_root, filename + ".md"))
        possible_paths.append(os.path.join(memory_root, filename.replace("_", "-") + ".md"))

    # 去重
    return list(set(possible_paths))


def _collect_index_identifiers(path: str, search_results: List[Dict[str, Any]]) -> List[str]:
    """收集所有需要清理索引的标识符"""
    identifiers_to_clean = []

    # 从搜索结果中提取permalink
    if search_results:
        for item in search_results:
            permalink = item.get("permalink", "")
            if permalink:
                identifiers_to_clean.append(permalink)

                # 处理不同格式的permalink
                if "-" in permalink:
                    identifiers_to_clean.append(permalink.replace("-", "_"))
                elif "_" in permalink:
                    identifiers_to_clean.append(permalink.replace("_", "-"))

    # 添加原始路径
    identifiers_to_clean.append(path)

    # 添加基础变体
    if "_" in path:
        identifiers_to_clean.append(path.replace("_", "-"))
    if "-" in path:
        identifiers_to_clean.append(path.replace("-", "_"))

    # 处理嵌套路径
    if "/" in path:
        folder, filename = path.split("/", 1)
        identifiers_to_clean.append(filename)
        if "_" in filename:
            identifiers_to_clean.append(filename.replace("_", "-"))
        if "-" in filename:
            identifiers_to_clean.append(filename.replace("-", "_"))

    # 去重
    return list(set(identifiers_to_clean))
