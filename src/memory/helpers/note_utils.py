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

        # 解析Basic Memory返回的Markdown格式输出
        logger.info(f"Basic Memory返回结果:\n{stdout}")

        # 初始化变量
        file_path = ""
        permalink = ""
        checksum = ""
        tags_list = []

        # 使用正则表达式提取关键信息
        import re

        # 提取file_path
        file_path_match = re.search(r"file_path:\s*([^\n]+)", stdout)
        if file_path_match:
            file_path = file_path_match.group(1).strip()
            logger.info(f"提取到file_path: {file_path}")

        # 提取permalink
        permalink_match = re.search(r"permalink:\s*([^\n]+)", stdout)
        if permalink_match:
            permalink = permalink_match.group(1).strip()
            logger.info(f"提取到permalink: {permalink}")

        # 提取checksum
        checksum_match = re.search(r"checksum:\s*([^\n]+)", stdout)
        if checksum_match:
            checksum = checksum_match.group(1).strip()
            logger.info(f"提取到checksum: {checksum}")

        # 提取tags
        tags_section = re.search(r"## Tags\s*([\s\S]*?)(?:##|$)", stdout)
        if tags_section:
            tags_content = tags_section.group(1).strip()
            tags_list = [tag.strip("- \n") for tag in tags_content.split("\n") if tag.strip().startswith("-")]
            logger.info(f"提取到tags: {tags_list}")

        # 构建结果字典
        result = {
            "title": title,
            "folder": folder.replace("_", "-"),  # 使用连字符格式
            "tags": tags_list if tags_list else (tags.split(",") if tags else []),
            "checksum": checksum,
        }

        # 构建存储路径
        storage_path = ""
        display_path = ""

        # 优先使用Basic Memory返回的permalink
        if permalink:
            storage_path = permalink
            # 确保有.md后缀用于显示
            display_path = storage_path
            if not display_path.endswith(".md"):
                display_path += ".md"
            # 更新结果中的permalink
            result["permalink"] = permalink
        # 其次使用file_path
        elif file_path:
            storage_path = file_path
            if storage_path.endswith(".md"):
                display_path = storage_path
                storage_path = storage_path[:-3]  # 移除.md后缀用于存储
            else:
                display_path = storage_path + ".md"
            # 更新结果中的permalink
            result["permalink"] = storage_path
        # 如果都没有，使用传入的参数构建路径
        else:
            folder_hyphen = folder.replace("_", "-")
            title_hyphen = title.replace("_", "-")
            storage_path = f"{folder_hyphen}/{title_hyphen}"
            display_path = f"{folder_hyphen}/{title_hyphen}.md"
            # 更新结果中的permalink
            result["permalink"] = storage_path

        # 确保 permalink 有正确的格式
        if not result["permalink"].startswith("memory://") and not result["permalink"].startswith("http"):
            result["permalink"] = f"memory://{result['permalink']}"

        # 记录实际的存储路径，便于调试
        logger.info(f"实际存储路径: {storage_path}, 显示路径: {display_path}")

        # 计算字数
        word_count = len(processed_content.split())

        # 使用显示路径构建成功消息
        tags_display = tags or "无"
        if isinstance(result["tags"], list) and result["tags"]:
            tags_display = ", ".join(result["tags"])

        success_message = f"📝 内容已保存!\n存储位置: {display_path}\n标签: {tags_display}\n字数: {word_count}字"
        logger.info(f"笔记已保存，实际存储路径: {storage_path}, 显示路径: {display_path}")

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

        # 预处理路径，移除可能的.md后缀
        clean_path = path
        if clean_path.endswith(".md"):
            clean_path = clean_path[:-3]  # 移除.md后缀
            logger.info(f"移除.md后缀，处理后的路径: {clean_path}")

        # 尝试不同的路径变体
        possible_paths = _generate_path_variants(clean_path)

        # 特别添加Basic Memory的路径格式
        if "/" in clean_path:
            parts = clean_path.split("/")
            if len(parts) >= 2:
                folder = parts[0]
                filename = parts[-1]

                # 使用连字符格式
                folder_hyphen = folder.replace("_", "-")
                filename_hyphen = filename.replace("_", "-")

                # 直接添加Basic Memory的路径格式
                basic_memory_path = f"{folder_hyphen}/{filename_hyphen}"
                possible_paths.insert(0, basic_memory_path)  # 将这个路径放在最前面

                # 如果文件名有.md后缀，尝试移除后缀
                if filename_hyphen.endswith(".md"):
                    basic_memory_path_no_md = f"{folder_hyphen}/{filename_hyphen[:-3]}"
                    possible_paths.insert(1, basic_memory_path_no_md)

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
                    logger.info(f"Basic Memory返回结果:\n{result.stdout}")

                    # 检查是否是错误消息（如"Note Not Found"）
                    if "Note Not Found" in result.stdout:
                        logger.warning(f"笔记未找到: {try_path}")
                        continue

                    # 解析Markdown格式的输出
                    import re

                    # 初始化变量
                    title = os.path.basename(try_path)
                    content = result.stdout
                    permalink = try_path
                    folder = try_path.split("/")[0] if "/" in try_path else "notes"
                    tags_list = []
                    checksum = ""

                    # 尝试提取元数据
                    # 提取标题
                    title_match = re.search(r"# ([^\n]+)", result.stdout)
                    if title_match:
                        title = title_match.group(1).strip()

                    # 提取permalink
                    permalink_match = re.search(r"permalink:\s*([^\n]+)", result.stdout)
                    if permalink_match:
                        permalink = permalink_match.group(1).strip()

                    # 提取checksum
                    checksum_match = re.search(r"checksum:\s*([^\n]+)", result.stdout)
                    if checksum_match:
                        checksum = checksum_match.group(1).strip()

                    # 提取tags
                    tags_section = re.search(r"## Tags\s*([\s\S]*?)(?:##|$)", result.stdout)
                    if tags_section:
                        tags_content = tags_section.group(1).strip()
                        tags_list = [tag.strip("- \n") for tag in tags_content.split("\n") if tag.strip().startswith("-")]

                    # 构建输出数据
                    output_data = {
                        "content": content,
                        "title": title,
                        "folder": folder,
                        "tags": tags_list,
                        "permalink": permalink,
                        "checksum": checksum,
                    }

                    # 确保 permalink 有正确的格式
                    if not output_data["permalink"].startswith("memory://") and not output_data["permalink"].startswith("http"):
                        output_data["permalink"] = f"memory://{output_data['permalink']}"

                    # 记录成功的路径格式，便于后续使用
                    logger.info(f"成功读取的路径格式: {try_path}")
                    logger.info(f"解析的元数据: {output_data}")

                    return True, content, output_data

        # 所有尝试失败
        logger.error(f"所有路径变体尝试失败，无法找到文档: {path}")
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

        # 获取标题信息
        title = existing_data.get("title", "")

        # 如果标题包含路径，只取最后一部分
        if "/" in title:
            title = title.split("/")[-1]

        # 如果标题仍然为空，使用路径的最后一部分
        if not title:
            title = os.path.basename(path)
            if "/" in title:
                title = title.split("/")[-1]

        # 使用permalink中的文件夹信息，避免路径嵌套
        permalink = existing_data.get("permalink", "")
        folder = "notes"  # 默认文件夹
        original_permalink = ""

        if permalink:
            logger.info(f"使用permalink获取文件夹信息: {permalink}")
            # 保存原始permalink，用于更新
            original_permalink = permalink

            # 如果有permalink，优先使用它来提取文件夹
            clean_permalink = permalink
            if permalink.startswith("memory://"):
                clean_permalink = permalink[9:]

            # 只取第一级目录
            if "/" in clean_permalink:
                folder = clean_permalink.split("/")[0]

                # 从第二部分提取文件名，可能是真正的标题
                filename_part = clean_permalink.split("/", 1)[1]
                if filename_part and filename_part != title:
                    # 如果文件名部分与当前标题不同，使用它作为标题
                    if filename_part.endswith(".md"):
                        filename_part = filename_part[:-3]
                    title = filename_part
        elif "/" in path:
            # 如果没有permalink，使用路径的第一部分
            folder = path.split("/")[0]

        # 检查标题中是否包含文件夹名，如果有则移除
        if folder in title:
            title = title.replace(folder + "_", "").replace(folder + "-", "")
            if not title:
                # 如果移除后标题为空，使用路径的最后一部分
                title = os.path.basename(path)
                if "/" in title:
                    title = title.split("/")[-1]
                if title.endswith(".md"):
                    title = title[:-3]

        # 移除标题中的.md后缀
        if title.endswith(".md"):
            title = title[:-3]

        # 使用连字符而非下划线，与Basic Memory的格式保持一致
        folder = folder.replace("_", "-")

        # 如果有原始permalink，尝试直接更新该笔记
        if original_permalink and original_permalink.startswith("memory://"):
            # 尝试使用原始permalink中的路径更新
            try:
                # 构建更新命令
                update_cmd = ["basic-memory", "tool", "update-note", original_permalink[9:], "--content", content]
                if tags:
                    update_cmd.extend(["--tags", tags])

                logger.info(f"尝试直接更新笔记: {' '.join(update_cmd)}")
                update_result = subprocess.run(update_cmd, capture_output=True, text=True, check=False)

                if update_result.returncode == 0:
                    logger.info(f"直接更新笔记成功: {original_permalink}")
                    # 解析返回结果
                    import re

                    # 提取permalink
                    permalink_match = re.search(r"permalink:\s*([^\n]+)", update_result.stdout)
                    if permalink_match:
                        permalink = permalink_match.group(1).strip()
                        if not permalink.startswith("memory://"):
                            permalink = f"memory://{permalink}"

                    # 构建结果
                    result = {
                        "title": title,
                        "folder": folder,
                        "tags": tags.split(",") if tags else [],
                        "permalink": permalink or original_permalink,
                        "content": content,
                    }

                    # 计算字数
                    word_count = len(content.split())

                    # 构建成功消息
                    display_path = permalink[9:] if permalink.startswith("memory://") else permalink
                    if not display_path.endswith(".md"):
                        display_path += ".md"

                    tags_display = tags or "无"
                    if isinstance(result["tags"], list) and result["tags"]:
                        tags_display = ", ".join(result["tags"])

                    success_message = f"📝 内容已更新!\n存储位置: {display_path}\n标签: {tags_display}\n字数: {word_count}字"

                    return True, success_message, result
            except Exception as e:
                logger.warning(f"直接更新笔记失败: {str(e)}")
                # 失败时继续使用创建方式更新

        logger.info(f"更新文档: 标题={title}, 文件夹={folder}")

        # 调用创建函数来更新笔记
        return create_note(content, title, folder, tags, project)

    except Exception as e:
        error_message = f"更新内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


def delete_note(path: str, memory_root: str, force: bool = False, project: str = "vibecopilot") -> Tuple[bool, str, Dict[str, Any]]:
    """
    删除笔记，只删除本地文件

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

        # 确保路径有.md后缀
        file_path = path
        if not file_path.endswith(".md"):
            file_path = file_path + ".md"

        # 构建完整的文件路径
        full_path = os.path.join(memory_root, file_path)
        logger.info(f"尝试删除文件: {full_path}")

        # 删除文件
        deleted = False
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                deleted = True
                logger.info(f"成功删除文件: {full_path}")
            except Exception as e:
                logger.error(f"删除文件 {full_path} 失败: {str(e)}")
                return False, f"删除文件失败: {str(e)}", {}

        # 处理删除结果
        if not deleted:
            # 即使没有找到文件，也返回成功，因为我们的目标是确保文件不存在
            return True, f"🗑️ 已删除文档（文件不存在）: {path}", {"permalink": path, "status": "not_found_but_ok"}

        # 成功删除文件
        return True, f"🗑️ 已删除文档: {path}", {"permalink": path, "deleted_file": full_path}

    except Exception as e:
        error_message = f"删除内容失败: {str(e)}"
        logger.error(error_message)
        return False, error_message, {}


# 辅助函数
def _generate_path_variants(path: str) -> List[str]:
    """生成路径的各种变体以提高查找成功率"""
    logger.info(f"为路径生成变体: {path}")
    possible_paths = [path]

    # 处理.md后缀
    has_md_suffix = path.endswith(".md")
    base_path = path[:-3] if has_md_suffix else path

    # 将基本路径添加到可能路径列表
    if base_path != path:
        possible_paths.append(base_path)

    # 处理memory://前缀
    if path.startswith("memory://"):
        # 移除前缀并添加到变体列表
        clean_path = path[9:]
        possible_paths.append(clean_path)
        # 如果有.md后缀，也添加没有.md的版本
        if clean_path.endswith(".md"):
            possible_paths.append(clean_path[:-3])
        else:
            # 如果没有.md后缀，添加带.md的版本
            possible_paths.append(clean_path + ".md")
        # 继续使用clean_path生成其他变体
        path = clean_path

    # 确保我们有带和不带.md后缀的版本
    if not has_md_suffix:
        possible_paths.append(path + ".md")

    # 连字符与下划线变体 - 对基本路径处理
    if "_" in base_path:
        hyphen_path = base_path.replace("_", "-")
        possible_paths.append(hyphen_path)
        # 添加带和不带.md的版本
        possible_paths.append(hyphen_path + ".md")
    if "-" in base_path:
        underscore_path = base_path.replace("-", "_")
        possible_paths.append(underscore_path)
        # 添加带和不带.md的版本
        possible_paths.append(underscore_path + ".md")

    # 处理带路径分隔符的情况
    if "/" in base_path:
        # 使用split而不是os.path.split，以便更精确地控制分割
        parts = base_path.split("/")

        if len(parts) >= 2:
            folder = parts[0]
            filename = parts[-1]  # 取最后一部分作为文件名

            # 生成所有可能的文件夹和文件名组合
            folder_variants = [folder, folder.replace("_", "-"), folder.replace("-", "_")]
            filename_variants = [filename, filename.replace("_", "-"), filename.replace("-", "_")]

            # 生成所有组合
            for f in folder_variants:
                for fn in filename_variants:
                    # 不带.md后缀
                    possible_paths.append(f"{f}/{fn}")
                    # 带.md后缀
                    possible_paths.append(f"{f}/{fn}.md")

            # 处理可能的嵌套路径问题
            if len(parts) > 2 or (folder in filename):
                # 如果路径有多级或文件夹名出现在文件名中，可能存在嵌套问题
                logger.info(f"检测到可能的路径嵌套问题: {base_path}")

                # 尝试只使用文件名部分
                for fn in filename_variants:
                    possible_paths.append(fn)
                    possible_paths.append(fn + ".md")

                # 如果文件名包含文件夹名，尝试移除这部分
                if folder in filename:
                    for prefix in [folder + "_", folder + "-"]:
                        if prefix in filename:
                            clean_filename = filename.replace(prefix, "")
                            if clean_filename:
                                # 添加带和不带.md的版本
                                possible_paths.append(clean_filename)
                                possible_paths.append(clean_filename + ".md")
                                # 添加带文件夹的版本
                                for f in folder_variants:
                                    possible_paths.append(f"{f}/{clean_filename}")
                                    possible_paths.append(f"{f}/{clean_filename}.md")

    # 特别处理Basic Memory的路径格式
    # 添加quick-test-folder/quick-test-note格式
    if "/" in path:
        # 将整个路径中的下划线替换为连字符
        all_hyphen_path = path.replace("_", "-")
        possible_paths.append(all_hyphen_path)
        if not all_hyphen_path.endswith(".md"):
            possible_paths.append(all_hyphen_path + ".md")

        # 尝试直接使用permalink格式
        parts = path.split("/")
        if len(parts) >= 2:
            folder = parts[0]
            filename = parts[-1]

            # 尝试使用连字符格式的permalink
            folder_hyphen = folder.replace("_", "-")
            filename_hyphen = filename.replace("_", "-")
            permalink_format = f"{folder_hyphen}/{filename_hyphen}"
            possible_paths.append(permalink_format)

            # 如果文件名有.md后缀，尝试移除后缀
            if filename_hyphen.endswith(".md"):
                permalink_format_no_md = f"{folder_hyphen}/{filename_hyphen[:-3]}"
                possible_paths.append(permalink_format_no_md)

    # 去重
    unique_paths = list(dict.fromkeys(possible_paths))
    logger.info(f"生成的路径变体: {unique_paths}")
    return unique_paths


def _extract_folder(path: str, existing_data: Dict[str, Any]) -> str:
    """从路径和现有数据中提取文件夹名称"""
    # 从path提取文件夹部分
    path_folder = ""
    if "/" in path:
        path_folder = path.split("/")[0]

    # 从existing_data中提取文件夹信息
    existing_folder = ""

    # 首先尝试从permalink提取
    permalink = existing_data.get("permalink", "")
    if permalink and isinstance(permalink, str):
        # 清理可能的路径前缀
        clean_permalink = permalink
        if permalink.startswith("memory://"):
            clean_permalink = permalink[9:]

        # 从permalink提取文件夹
        if "/" in clean_permalink:
            existing_folder = clean_permalink.split("/")[0]

    # 如果从permalink无法提取，尝试从folder字段提取
    if not existing_folder:
        folder_field = existing_data.get("folder", "")
        if folder_field and isinstance(folder_field, str):
            # 清理可能的路径前缀
            if folder_field.startswith("memory://"):
                folder_field = folder_field[9:]

            # 只取文件夹的第一部分，避免嵌套
            if "/" in folder_field:
                existing_folder = folder_field.split("/")[0]
            else:
                existing_folder = folder_field

    # 选择合适的文件夹名
    if existing_folder and existing_folder != path_folder:
        # 如果两者不同，且existing_folder非空，优先使用existing_folder
        # 使用连字符而非下划线，与Basic Memory的格式保持一致
        return existing_folder.replace("_", "-")
    elif path_folder:
        # 否则使用从path提取的文件夹（如果有）
        # 使用连字符而非下划线，与Basic Memory的格式保持一致
        return path_folder.replace("_", "-")
    else:
        # 如果都没有，使用默认值
        return "notes"


def _collect_delete_paths(path: str, search_results: List[Dict[str, Any]], memory_root: str) -> List[str]:
    """收集需要删除的文件路径"""
    # 根据permalink构建文件路径
    # 注意：permalink不带.md后缀，但文件路径需要.md后缀

    # 构建基本路径
    basic_path = os.path.join(memory_root, path + ".md")

    # 如果是路径格式，考虑连字符和下划线的变体
    if "/" in path:
        parts = path.split("/")
        if len(parts) >= 2:
            folder = parts[0]
            filename = parts[-1]

            # 构建可能的路径
            paths = [
                # 标准路径
                os.path.join(memory_root, folder, filename + ".md"),
                # 连字符变体
                os.path.join(memory_root, folder.replace("_", "-"), filename.replace("_", "-") + ".md"),
                # 下划线变体
                os.path.join(memory_root, folder.replace("-", "_"), filename.replace("-", "_") + ".md"),
                # 可能的嵌套路径
                os.path.join(memory_root, folder, folder, filename + ".md"),
            ]
            return paths

    # 如果不是路径格式，只返回基本路径
    return [basic_path]
