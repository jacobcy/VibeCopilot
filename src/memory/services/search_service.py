#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索服务 - 负责知识库内容的列表和搜索功能

封装Basic Memory搜索和列表功能的实现细节，提供简洁的API接口。
"""

import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务，处理知识库内容的列表和搜索"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化搜索服务

        Args:
            config: 可选配置参数
        """
        self.config = config or {}
        self.project = self.config.get("project", "vibecopilot")

    def list_notes(self, folder: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        列出知识库中的内容

        Args:
            folder: 筛选特定目录的内容（可选）

        Returns:
            元组，包含(是否成功, 消息, 结果列表)
        """
        try:
            logger.info(f"列出知识库内容: {'全部' if folder is None else f'目录: {folder}'}")

            # 构建命令
            if folder:
                # 如果指定了文件夹，使用搜索功能
                cmd = ["basic-memory", f"--project={self.project}", "tool", "search-notes", folder]
            else:
                # 否则使用最近活动功能
                cmd = ["basic-memory", f"--project={self.project}", "tool", "recent-activity"]

            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "获取知识库内容列表失败"
                return False, f"列出内容失败: {error_msg}", []

            try:
                # 解析输出结果
                output_data = json.loads(result.stdout)

                # 根据命令不同，获取结果列表
                if folder:
                    notes = output_data.get("results", [])
                else:
                    notes = output_data.get("primary_results", output_data.get("results", []))

            except json.JSONDecodeError:
                # 解析失败时使用简单处理
                notes = []
                for line in result.stdout.split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split(" - ", 1)
                    if len(parts) > 1:
                        notes.append({"title": parts[0].strip(), "file_path": parts[1].strip() if len(parts) > 1 else ""})

            # 处理结果
            if not notes:
                return True, "知识库中没有找到内容" + (f"（目录: {folder}）" if folder else ""), []

            # 格式化输出
            formatted_results = "\n".join(
                [
                    f"📄 {note.get('title', '无标题')} - [{note.get('file_path', note.get('permalink', 'default'))}] - {note.get('updated_at', '').split('T')[0] if note.get('updated_at') else note.get('created_at', '未知').split(' ')[0] if note.get('created_at') else ''}"
                    for note in notes
                ]
            )

            summary = f"找到 {len(notes)} 个文档:\n\n{formatted_results}"

            return True, summary, notes

        except Exception as e:
            error_message = f"列出知识库内容失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, []

    def search_notes(self, query: str, content_type: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        搜索知识库内容

        Args:
            query: 搜索关键词
            content_type: 内容类型（可选）

        Returns:
            元组，包含(是否成功, 消息, 结果列表)
        """
        try:
            logger.info(f"搜索知识库: {query}, 类型: {content_type or '全部'}")

            # 构建命令
            cmd = ["basic-memory", "tool", "search-notes", query]

            # 如果指定了content_type，使用types参数
            if content_type:
                cmd.extend(["--types", content_type])

            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "搜索知识库失败"
                return False, f"搜索失败: {error_msg}", []

            try:
                # 解析输出结果
                output_data = json.loads(result.stdout)
                search_results = output_data.get("results", [])

                # 如果没有找到结果，尝试使用text搜索方式
                if not search_results:
                    logger.info("未找到结果，尝试使用text搜索方式")
                    cmd = ["basic-memory", "tool", "search-notes", "--search-type", "text", query]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        try:
                            output_data = json.loads(result.stdout)
                            search_results = output_data.get("results", [])
                        except json.JSONDecodeError:
                            pass
            except json.JSONDecodeError:
                # 解析失败时使用简单处理
                search_results = []
                for line in result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split(" - ", 1)
                        if len(parts) > 1:
                            search_results.append({"title": parts[0].strip(), "content": parts[1].strip() if len(parts) > 1 else ""})

            # 处理结果
            if not search_results:
                return True, f"未找到与 '{query}' 相关的内容", []

            # 格式化搜索结果
            formatted_results = []
            for idx, item in enumerate(search_results, 1):
                title = item.get("title", "无标题")
                permalink = item.get("permalink", "")
                snippet = (
                    item.get("content_snippet", item.get("content", ""))[:100] + "..." if item.get("content_snippet") or item.get("content") else ""
                )
                formatted_results.append(f"{idx}. [{title}] - {permalink}\n   {snippet}")

            result_message = f"找到 {len(search_results)} 条与 '{query}' 相关的结果:\n\n" + "\n\n".join(formatted_results)

            return True, result_message, search_results

        except Exception as e:
            error_message = f"搜索知识库失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, []
