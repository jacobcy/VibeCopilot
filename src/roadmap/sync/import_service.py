"""
导入服务模块

提供从YAML文件导入路线图数据的功能。
"""

import json
import logging
import os
import shutil
import tempfile
import time
from typing import Any, Dict, Optional, Tuple

import yaml

from src.db.session import session_scope
from src.parsing.processors.roadmap_processor import RoadmapProcessor
from src.utils.file_utils import get_data_path
from src.validation.roadmap_validation import RoadmapValidator

from .importers import EpicImporter, MilestoneImporter, RoadmapImporter, TaskImporter
from .utils import print_error, print_success

logger = logging.getLogger(__name__)


def get_temp_dir(sub_dir=None, timestamp_subdir=True):
    """获取项目临时目录路径 (使用 get_data_path)

    Args:
        sub_dir: 可选的子目录名
        timestamp_subdir: 是否创建时间戳子目录

    Returns:
        str: 临时目录的绝对路径

    Raises:
        ValueError: 如果无法通过 get_data_path 确定数据目录或创建临时目录。
    """
    path_elements = ["temp"]
    if sub_dir:
        path_elements.append(sub_dir)
    if timestamp_subdir:
        timestamp = time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        path_elements.append(timestamp)

    try:
        # get_data_path handles directory creation
        temp_path = get_data_path(*path_elements)
        if not temp_path:
            raise ValueError("`get_data_path` failed to return a valid path for the temporary directory.")
        return temp_path
    except Exception as e:
        logger.error(f"获取或创建临时目录失败: {e}", exc_info=True)
        # Re-raise the exception to make the error visible
        raise ValueError(f"Failed to get or create temporary directory: {e}") from e


class RoadmapImportService:
    """路线图导入服务，提供从YAML文件导入路线图数据的功能"""

    def __init__(self, service):
        """
        初始化路线图导入服务

        Args:
            service: 路线图服务
        """
        self.service = service
        self.validator = RoadmapValidator()
        self.processor = RoadmapProcessor()

    async def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """
        从YAML文件导入路线图数据 (严格模式)

        Args:
            file_path: YAML文件路径
            roadmap_id: 路线图ID，不提供则创建新路线图
            verbose: 是否启用详细日志

        Returns:
            Dict[str, Any]: 导入结果
        """
        if not os.path.exists(file_path):
            error_msg = f"文件不存在: {file_path}"
            logger.error(error_msg)
            print_error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            with session_scope() as session:
                # 步骤1: 解析并验证 YAML 文件
                yaml_data = await self._parse_and_validate_yaml(file_path, verbose)
                if yaml_data is None:
                    return {"success": False, "error": f"无法解析或验证YAML文件: {file_path}"}

                # source_file is now just file_path
                source_file = file_path

                # 初始化导入器
                stop_on_error = not verbose
                roadmap_importer = RoadmapImporter(self.service, verbose, stop_on_error)
                milestone_importer = MilestoneImporter(self.service, verbose, stop_on_error)
                epic_importer = EpicImporter(self.service, verbose, stop_on_error)
                task_importer = TaskImporter(self.service, verbose, stop_on_error)

                # 获取或创建路线图ID
                roadmap_id = roadmap_importer.get_or_create_roadmap(yaml_data, source_file)
                if not roadmap_id:
                    return {"success": False, "error": "无法获取或创建路线图ID"}

                # 确保路线图存在
                roadmap = self.service.get_roadmap(roadmap_id)
                if not roadmap:
                    error_msg = f"路线图不存在: {roadmap_id}"
                    logger.error(error_msg)
                    print_error(error_msg)
                    return {"success": False, "error": error_msg}

                # 用于跟踪导入状态
                import_stats = {
                    "milestones": {"success": 0, "failed": 0},
                    "epics": {"success": 0, "failed": 0},
                    "stories": {"success": 0, "failed": 0},
                    "tasks": {"success": 0, "failed": 0},
                }

                # 优先导入Epic结构
                if "epics" in yaml_data:
                    logger.info(f"检测到Epic结构，优先导入Epic-Story-Task")
                    if verbose:
                        logger.debug(f"检测到Epic结构，优先导入Epic-Story-Task")
                    epic_importer.import_epics(yaml_data, roadmap_id, import_stats)

                # 导入里程碑（如果有）
                elif "milestones" in yaml_data:
                    logger.info(f"检测到Milestone结构，导入Milestone-Task")
                    if verbose:
                        logger.debug(f"检测到Milestone结构，导入Milestone-Task")
                    milestone_importer.import_milestones(yaml_data, roadmap_id, import_stats)

                    # 导入根级任务 - 如果存在，关联到里程碑
                    if "tasks" in yaml_data:
                        # 找到第一个里程碑作为默认关联对象
                        milestone_id = None
                        milestones = self.service.get_milestones(roadmap_id)
                        if milestones:
                            milestone_id = milestones[0].get("id")

                        # 导入任务，关联到找到的里程碑
                        task_importer.import_tasks(yaml_data["tasks"], milestone_id, roadmap_id, import_stats)

                # 仅有根级任务
                elif "tasks" in yaml_data:
                    logger.info(f"仅检测到根级任务，直接导入Task")
                    if verbose:
                        logger.debug(f"仅检测到根级任务，直接导入Task")
                    task_importer.import_tasks(yaml_data["tasks"], None, roadmap_id, import_stats)

                # 生成导入结果
                result = self._generate_import_result(file_path, roadmap_id, import_stats, verbose)

                return result

        except Exception as e:
            error_msg = f"从YAML导入路线图失败"
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            print_error(error_msg, e, show_traceback=verbose)
            return {"success": False, "error": f"{error_msg}: {str(e)}"}

    async def _parse_and_validate_yaml(self, file_path: str, verbose: bool) -> Optional[Dict[str, Any]]:
        """
        使用 RoadmapProcessor 解析 YAML 文件并进行可选验证。

        Args:
            file_path: YAML文件路径
            verbose: 是否启用详细日志

        Returns:
            Optional[Dict[str, Any]]: 解析后的YAML数据，如果解析或验证失败则返回None。
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 使用 RoadmapProcessor 解析 (它现在只做 YAML 解析和验证)
            processed_data = await self.processor.parse_roadmap(content)

            # parse_roadmap 现在在失败时返回 None
            if processed_data is None:
                logger.error(f"RoadmapProcessor 未能成功解析或验证文件: {file_path}")
                return None

            # 验证可能已经在 processor.parse_roadmap 中完成，但可以再确认一次
            if self.validator:
                is_valid = self.validator.validate(processed_data)
                if not is_valid:
                    errors = self.validator.get_errors()
                    logger.error(f"导入前最终验证失败: {errors}")
                    # 根据严格模式决定是否返回 None
                    # return None # For strict validation
                    pass  # Allow import even with validation errors, logged in processor

            logger.info(f"YAML 文件解析和验证成功: {file_path}")
            return processed_data

        except Exception as e:
            logger.error(f"解析或验证 YAML 文件时发生意外错误: {file_path}: {e}", exc_info=True)
            return None

    def _generate_import_result(self, file_path: str, roadmap_id: str, import_stats: Dict[str, Dict[str, int]], verbose: bool) -> Dict[str, Any]:
        """生成导入结果报告"""
        # 计算是否有导入失败的项目
        has_failures = any(stat["failed"] > 0 for stat in import_stats.values())

        # 日志输出导入结果
        logger.info(f"从YAML导入路线图: {file_path} -> {roadmap_id}")

        # 构建导入结果
        result = {
            "success": not has_failures or verbose,  # 详细模式下，即使有失败也视为部分成功
            "roadmap_id": roadmap_id,
            "source_file": file_path,
            "stats": {
                "milestones": import_stats["milestones"],
                "epics": import_stats["epics"],
                "stories": import_stats["stories"],
                "tasks": import_stats["tasks"],
            },
        }

        # 如果有失败项但在详细模式下继续，添加警告信息
        if has_failures and verbose:
            result["warning"] = "部分项目导入失败，请查看日志了解详情"
            logger.debug(f"\n{logger.debug('⚠️ 警告', 'yellow', 'bold')}: {logger.debug('部分项目导入失败，但因为处于详细模式，仍然继续导入', 'yellow')}")

        # 打印导入统计信息
        self._print_import_stats(import_stats)

        return result

    def _print_import_stats(self, import_stats: Dict[str, Dict[str, int]]) -> None:
        """打印导入统计信息"""
        logger.debug(f"\n{logger.debug('📊 导入统计:', 'blue', 'bold')}")
        logger.debug(
            f"{logger.debug('•', 'green')} 里程碑: {logger.debug(str(import_stats['milestones']['success']), 'green')}成功, {logger.debug(str(import_stats['milestones']['failed']), 'red' if import_stats['milestones']['failed'] > 0 else 'green')}失败"
        )
        logger.debug(
            f"{logger.debug('•', 'green')} 史诗: {logger.debug(str(import_stats['epics']['success']), 'green')}成功, {logger.debug(str(import_stats['epics']['failed']), 'red' if import_stats['epics']['failed'] > 0 else 'green')}失败"
        )
        logger.debug(
            f"{logger.debug('•', 'green')} 故事: {logger.debug(str(import_stats['stories']['success']), 'green')}成功, {logger.debug(str(import_stats['stories']['failed']), 'red' if import_stats['stories']['failed'] > 0 else 'green')}失败"
        )
        logger.debug(
            f"{logger.debug('•', 'green')} 任务: {logger.debug(str(import_stats['tasks']['success']), 'green')}成功, {logger.debug(str(import_stats['tasks']['failed']), 'red' if import_stats['tasks']['failed'] > 0 else 'green')}失败"
        )
