#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步工具模块

提供文件与知识库的同步功能、知识库导出和监控功能。
"""

import glob
import json
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def sync_file(file_path: str, folder: str = "default", project: str = "vibecopilot") -> bool:
    """
    将单个文件同步到知识库

    Args:
        file_path: 待同步文件路径
        folder: 目标文件夹
        project: 项目名称

    Returns:
        bool: 同步是否成功
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False

    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 构建同步命令
        cmd = [
            "basic-memory",
            "tool",
            "write-note",
            f"--title={os.path.basename(file_path)}",
            f"--folder={folder}",
            f"--content={content}",
        ]

        # 执行命令
        logger.info(f"正在同步文件到知识库: {file_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"文件同步成功: {file_path}")
            return True
        else:
            logger.error(f"文件同步失败: {file_path}, 错误: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"同步文件时发生异常: {file_path}, 错误: {str(e)}")
        return False


def sync_files(file_paths: List[str], folder: str = "default", project: str = "vibecopilot") -> Dict[str, bool]:
    """
    同步多个文件到知识库

    Args:
        file_paths: 待同步文件路径列表
        folder: 目标文件夹
        project: 项目名称

    Returns:
        Dict[str, bool]: 文件路径到同步结果的映射
    """
    results = {}

    for file_path in file_paths:
        results[file_path] = sync_file(file_path, folder, project)

    # 输出同步结果摘要
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"同步完成: 成功 {success_count}/{len(file_paths)} 个文件")

    return results


def export_knowledge_base(output_dir: str, output_format: str = "md", project: str = "vibecopilot") -> bool:
    """
    导出知识库内容到指定目录

    Args:
        output_dir: 输出目录
        output_format: 输出格式 (md, json, csv)
        project: 项目名称

    Returns:
        bool: 导出是否成功
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"创建输出目录: {output_dir}")

    try:
        # 构建导出命令
        cmd = ["basic-memory", "sync", f"--output={output_dir}", f"--format={output_format}"]

        # 执行命令
        logger.info(f"正在导出知识库到: {output_dir}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"知识库导出成功: {output_dir}")
            return True
        else:
            logger.error(f"知识库导出失败, 错误: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"导出知识库时发生异常, 错误: {str(e)}")
        return False


def start_sync_watch(project: str = "vibecopilot") -> subprocess.Popen:
    """
    开始监视知识库变化

    Args:
        project: 项目名称

    Returns:
        subprocess.Popen: 监视进程实例
    """
    try:
        # 构建监视命令
        cmd = [
            "basic-memory",
            "sync",
            "--watch",
        ]

        # 启动监视进程
        logger.info(f"正在启动知识库监视: {project}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        logger.info(f"知识库监视已启动, PID: {process.pid}")
        return process

    except Exception as e:
        logger.error(f"启动知识库监视时发生异常, 错误: {str(e)}")
        raise


def sync_directory(directory: str, pattern: str = "*.md", folder: str = "default", project: str = "vibecopilot") -> Dict[str, bool]:
    """
    同步目录中所有匹配模式的文件

    Args:
        directory: 目录路径
        pattern: 文件匹配模式
        folder: 目标文件夹
        project: 项目名称

    Returns:
        Dict[str, bool]: 文件路径到同步结果的映射
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        logger.error(f"目录不存在: {directory}")
        return {}

    # 查找匹配的文件
    file_pattern = os.path.join(directory, pattern)
    file_paths = glob.glob(file_pattern)

    if not file_paths:
        logger.warning(f"未找到匹配的文件: {file_pattern}")
        return {}

    logger.info(f"在目录 {directory} 中找到 {len(file_paths)} 个匹配文件")

    # 同步找到的文件
    return sync_files(file_paths, folder, project)


def get_sync_status(project: str = "vibecopilot") -> Dict[str, Any]:
    """
    获取知识库同步状态

    Args:
        project: 项目名称

    Returns:
        Dict[str, Any]: 同步状态信息
    """
    try:
        # 构建状态查询命令
        cmd = [
            "basic-memory",
            "status",
        ]

        # 执行命令
        logger.info(f"正在获取知识库同步状态: {project}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 解析JSON输出
            try:
                status = json.loads(result.stdout)
                logger.info(f"知识库同步状态获取成功")
                return status
            except json.JSONDecodeError:
                logger.error(f"解析同步状态JSON失败: {result.stdout}")
                return {"error": "解析JSON失败", "raw_output": result.stdout}
        else:
            logger.error(f"获取知识库同步状态失败, 错误: {result.stderr}")
            return {"error": result.stderr}

    except Exception as e:
        logger.error(f"获取知识库同步状态时发生异常, 错误: {str(e)}")
        return {"error": str(e)}
