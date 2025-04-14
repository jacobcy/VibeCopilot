#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证操作

提供工作流的验证功能。
"""

import logging
import os
from typing import Any, Dict

from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file
from src.workflow.service.base import get_workflows_directory

logger = logging.getLogger(__name__)


def validate_workflow_files(workflow_dir: str = None, auto_fix: bool = False) -> Dict[str, Any]:
    """
    验证工作流文件，确保ID与文件名一致

    Args:
        workflow_dir: 工作流目录（可选，默认使用配置的工作流目录）
        auto_fix: 是否自动修复不一致的文件

    Returns:
        Dict[str, Any]: 包含验证结果的字典
        {
            "valid": 有效文件数,
            "invalid": 无效文件数,
            "fixed": 修复的文件数,
            "details": [
                {
                    "file": 文件名,
                    "id": ID,
                    "status": "valid|invalid|fixed",
                    "issue": 问题描述（如果有）
                },
                ...
            ]
        }
    """
    if workflow_dir is None:
        workflow_dir = get_workflows_directory()

    ensure_directory_exists(workflow_dir)

    result = {"valid": 0, "invalid": 0, "fixed": 0, "details": []}

    # 遍历所有工作流文件
    for filename in os.listdir(workflow_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(workflow_dir, filename)
        try:
            workflow_data = read_json_file(file_path)

            # 检查是否有ID
            if "id" not in workflow_data:
                detail = {"file": filename, "id": None, "status": "invalid", "issue": "缺少ID字段"}
                result["invalid"] += 1

                # 自动修复：为工作流添加ID（使用文件名，不含后缀）
                if auto_fix:
                    new_id = filename.split(".")[0]
                    workflow_data["id"] = new_id
                    if write_json_file(file_path, workflow_data):
                        detail["status"] = "fixed"
                        detail["id"] = new_id
                        result["fixed"] += 1
                        logger.info(f"已为工作流 {filename} 添加ID: {new_id}")
                    else:
                        logger.error(f"修复工作流 {filename} 失败")

                result["details"].append(detail)
                continue

            # 获取工作流ID
            workflow_id = workflow_data["id"]
            expected_filename = f"{workflow_id}.json"

            # 检查文件名是否与ID一致
            if filename != expected_filename:
                detail = {"file": filename, "id": workflow_id, "status": "invalid", "issue": f"文件名与ID不匹配，期望文件名: {expected_filename}"}
                result["invalid"] += 1

                # 自动修复：重命名文件或更新ID
                if auto_fix:
                    # 检查是否已存在与ID匹配的文件
                    if os.path.exists(os.path.join(workflow_dir, expected_filename)):
                        # 已存在同ID文件，更新当前文件的ID
                        new_id = filename.split(".")[0]
                        workflow_data["id"] = new_id
                        if write_json_file(file_path, workflow_data):
                            detail["status"] = "fixed"
                            detail["issue"] += f"，已更新ID为: {new_id}"
                            result["fixed"] += 1
                            logger.info(f"已更新工作流 {filename} 的ID: {workflow_id} -> {new_id}")
                        else:
                            logger.error(f"修复工作流 {filename} 失败")
                    else:
                        # 不存在同ID文件，重命名当前文件
                        new_path = os.path.join(workflow_dir, expected_filename)
                        try:
                            os.rename(file_path, new_path)
                            detail["status"] = "fixed"
                            detail["issue"] += "，已重命名文件"
                            result["fixed"] += 1
                            logger.info(f"已重命名工作流文件: {filename} -> {expected_filename}")
                        except Exception as e:
                            logger.error(f"重命名工作流文件失败: {filename} -> {expected_filename}, 错误: {str(e)}")

                result["details"].append(detail)
                continue

            # 文件有效
            result["valid"] += 1
            result["details"].append({"file": filename, "id": workflow_id, "status": "valid"})

        except Exception as e:
            result["invalid"] += 1
            result["details"].append({"file": filename, "id": None, "status": "invalid", "issue": f"读取或处理文件时出错: {str(e)}"})
            logger.error(f"验证工作流文件 {filename} 时出错: {str(e)}")

    return result
