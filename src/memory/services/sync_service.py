#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步服务 - 负责本地内容与Basic Memory的同步

封装Basic Memory同步功能的实现细节，提供简洁的API接口。
"""

import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from ..helpers.sync_tools import export_knowledge_base, get_sync_status
from ..helpers.sync_tools import start_sync_watch as start_watch
from ..helpers.sync_tools import sync_directory, sync_file, sync_files
from ..helpers.sync_utils import create_sync_payload, get_sync_config, load_sync_payload, save_sync_config, save_sync_payload, update_last_sync_time

logger = logging.getLogger(__name__)


class SyncService:
    """同步服务，处理本地内容与Basic Memory的同步"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化同步服务

        Args:
            config: 可选配置参数
        """
        self.config = config or {}
        self.project = self.config.get("project", "vibecopilot")
        self.memory_root = os.path.expanduser(self.config.get("memory_root", "~/Public/VibeCopilot/.ai/memory"))
        self.rules_dir = self.config.get("rules_dir", "rules")
        self.docs_dir = self.config.get("docs_dir", "docs")

    def sync_rules(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        同步规则文件到知识库

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info("同步规则文件到知识库")

            # 获取规则文件列表
            rules_path = os.path.join(os.path.expanduser("~/Public/VibeCopilot"), self.rules_dir)
            rule_files = glob.glob(os.path.join(rules_path, "**/*.md"), recursive=True)
            rule_files.extend(glob.glob(os.path.join(rules_path, "**/*.mdc"), recursive=True))

            if not rule_files:
                return True, "没有找到规则文件", {"SYNCED": 0, "failed": 0}

            # 使用sync_files函数同步文件
            results = sync_files(rule_files, folder="rules", project=self.project)

            # 统计结果
            success_count = sum(1 for success in results.values() if success)
            fail_count = len(results) - success_count

            # 生成结果消息
            message = f"规则同步完成: 成功 {success_count} 个，失败 {fail_count} 个"
            if fail_count > 0:
                failed_files = [f for f, success in results.items() if not success]
                message += f"\n失败的文件: {', '.join(os.path.basename(f) for f in failed_files)}"

            # 更新最后同步时间
            update_last_sync_time()

            return True, message, {"SYNCED": success_count, "failed": fail_count, "details": results}

        except Exception as e:
            error_message = f"同步规则失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def sync_documents(self, files: Optional[List[str]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        同步文档文件到知识库

        Args:
            files: 要同步的文件列表，如果为None则同步所有文档

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info(f"同步文档到知识库: {files if files else '所有文档'}")

            # 如果没有指定文件，使用sync_directory函数
            if not files:
                docs_path = os.path.join(os.path.expanduser("~/Public/VibeCopilot"), self.docs_dir)
                results = sync_directory(directory=docs_path, folder="docs", pattern="**/*.md", project=self.project)
            else:
                # 如果指定了文件，使用sync_files函数
                if not files:
                    return True, "没有找到文档文件", {"SYNCED": 0, "failed": 0}
                results = sync_files(files, folder="docs", project=self.project)

            # 统计结果
            success_count = sum(1 for success in results.values() if success)
            fail_count = len(results) - success_count

            # 生成结果消息
            message = f"文档同步完成: 成功 {success_count} 个，失败 {fail_count} 个"
            if fail_count > 0:
                failed_files = [f for f, success in results.items() if not success]
                message += f"\n失败的文件: {', '.join(os.path.basename(f) for f in failed_files)}"

            # 更新最后同步时间
            update_last_sync_time()

            return True, message, {"SYNCED": success_count, "failed": fail_count, "details": results}

        except Exception as e:
            error_message = f"同步文档失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def sync_all(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        同步所有内容到知识库

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info("同步所有内容到知识库")

            # 同步规则
            rules_success, rules_message, rules_result = self.sync_rules()

            # 同步文档
            docs_success, docs_message, docs_result = self.sync_documents()

            # 合并结果
            synced_count = rules_result.get("SYNCED", 0) + docs_result.get("SYNCED", 0)
            failed_count = rules_result.get("failed", 0) + docs_result.get("failed", 0)

            message = f"全部同步完成: 成功 {synced_count} 个，失败 {failed_count} 个\n"
            message += f"- 规则: {rules_result.get('synced', 0)} 成功，{rules_result.get('failed', 0)} 失败\n"
            message += f"- 文档: {docs_result.get('synced', 0)} 成功，{docs_result.get('failed', 0)} 失败"

            return True, message, {"SYNCED": synced_count, "failed": failed_count, "rules": rules_result, "docs": docs_result}

        except Exception as e:
            error_message = f"同步所有内容失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def import_documents(self, source_dir: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        从外部目录导入文档到知识库

        Args:
            source_dir: 源目录路径

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info(f"从 {source_dir} 导入文档")

            # 验证源目录
            source_dir = os.path.expanduser(source_dir)
            if not os.path.exists(source_dir):
                return False, f"源目录不存在: {source_dir}", {}

            # 使用sync_directory函数导入文件
            results = sync_directory(directory=source_dir, folder="imported", pattern="**/*.md", project=self.project)

            # 统计结果
            success_count = sum(1 for success in results.values() if success)
            fail_count = len(results) - success_count

            # 生成结果消息
            message = f"文档导入完成: 成功 {success_count} 个，失败 {fail_count} 个"
            if fail_count > 0:
                failed_files = [f for f, success in results.items() if not success]
                message += f"\n失败的文件: {', '.join(os.path.basename(f) for f in failed_files)}"

            return True, message, {"imported": success_count, "failed": fail_count, "details": results}

        except Exception as e:
            error_message = f"导入文档失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def export_documents(self, output_dir: Optional[str] = None, format_type: str = "md") -> Tuple[bool, str, Dict[str, Any]]:
        """
        导出知识库内容到本地目录

        Args:
            output_dir: 输出目录，如果为None则使用默认目录
            format_type: 导出格式，如md、json等

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info(f"导出知识库内容: 格式={format_type}, 目标目录={output_dir or '默认'}")

            # 使用export_knowledge_base函数导出知识库
            export_path = export_knowledge_base(output_dir=output_dir, output_format=format_type, project=self.project)

            if not export_path:
                return False, "导出知识库失败", {}

            # 统计导出的文件数量
            exported_files = []
            if os.path.isdir(export_path):
                for root, _, files in os.walk(export_path):
                    for file in files:
                        if file.endswith(f".{format_type}"):
                            exported_files.append(os.path.join(root, file))

            message = f"知识库内容已导出到 {export_path}，共 {len(exported_files)} 个文件"

            return True, message, {"export_path": export_path, "file_count": len(exported_files), "format": format_type}

        except Exception as e:
            error_message = f"导出知识库失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def start_sync_watch(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        启动知识库内容变更监控

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info("启动知识库内容变更监控")

            # 使用start_watch函数启动监控
            process = start_watch(project=self.project)

            if not process:
                return False, "启动知识库监控失败", {}

            return True, "知识库内容变更监控已启动，按Ctrl+C停止", {"watching": True, "process_pid": process.pid}

        except Exception as e:
            error_message = f"启动知识库内容变更监控失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def get_status(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        获取同步状态信息

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info("获取同步状态")

            # 使用get_sync_status获取状态
            status_data = get_sync_status(project=self.project)

            if not status_data:
                return False, "获取同步状态失败", {}

            # 获取同步配置
            config = get_sync_config()

            # 合并状态和配置信息
            result = {**status_data, "config": config}

            return True, "获取同步状态成功", result

        except Exception as e:
            error_message = f"获取同步状态失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}

    def save_sync_data(self, data: Dict[str, Any], file_path: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        保存同步数据到文件

        Args:
            data: 要保存的数据
            file_path: 保存路径，如果为None则使用默认路径

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        try:
            logger.info(f"保存同步数据: {file_path or '默认路径'}")

            if file_path is None:
                file_path = os.path.join(self.memory_root, "sync", "latest_sync.json")

            # 创建同步负载
            payload = create_sync_payload(data.get("items", []))

            # 保存负载
            success = save_sync_payload(payload, file_path)

            if not success:
                return False, "保存同步数据失败", {}

            return True, f"同步数据已保存到 {file_path}", {"file_path": file_path, "item_count": payload.get("item_count", 0)}

        except Exception as e:
            error_message = f"保存同步数据失败: {str(e)}"
            logger.error(error_message)
            return False, error_message, {}
