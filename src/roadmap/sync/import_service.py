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

from src.validation.roadmap_validation import RoadmapValidator

from .importers import EpicImporter, MilestoneImporter, RoadmapImporter, TaskImporter
from .utils import colorize, print_error, print_success

logger = logging.getLogger(__name__)


def get_temp_dir(sub_dir=None, timestamp_subdir=True):
    """获取项目临时目录路径

    Args:
        sub_dir: 可选的子目录名
        timestamp_subdir: 是否创建时间戳子目录

    Returns:
        str: 临时目录的绝对路径
    """
    # 获取当前时间戳作为目录名
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 确定项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    # 基础temp目录
    temp_dir = os.path.join(project_root, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # 如果提供了子目录名，则在temp下创建特定类型的子目录
    if sub_dir:
        # 创建类型子目录
        type_dir = os.path.join(temp_dir, sub_dir)
        os.makedirs(type_dir, exist_ok=True)

        # 如果需要创建时间戳子目录
        if timestamp_subdir:
            # 创建时间戳子目录
            timestamped_dir = os.path.join(type_dir, timestamp)
            os.makedirs(timestamped_dir, exist_ok=True)
            return timestamped_dir

        return type_dir

    # 如果没有提供子目录名，则直接返回基础temp目录
    return temp_dir


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

    def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False, force_llm: bool = False) -> Dict[str, Any]:
        """
        从YAML文件导入路线图数据

        Args:
            file_path: YAML文件路径
            roadmap_id: 路线图ID，不提供则创建新路线图
            verbose: 是否启用详细日志
            force_llm: 是否强制使用LLM解析YAML，不进行其他尝试

        Returns:
            Dict[str, Any]: 导入结果
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"文件不存在: {file_path}"
            logger.error(error_msg)
            print_error(error_msg)
            return {"success": False, "error": error_msg}

        try:
            # 步骤1: 验证并尝试修复YAML文件，如果指定了force_llm则强制使用LLM解析
            source_file, yaml_data = self._validate_and_fix_yaml(file_path, verbose, force_llm)
            if not yaml_data:
                return {"success": False, "error": f"YAML文件为空或格式不正确: {file_path}"}

            if source_file != file_path:
                logger.info(f"使用修复后的文件进行导入: {source_file}")
                if verbose:
                    print(colorize(f"使用修复后的文件进行导入: {source_file}", "cyan"))

            # 初始化导入器
            stop_on_error = not verbose  # 非详细模式下遇到错误就停止
            roadmap_importer = RoadmapImporter(self.service, verbose, stop_on_error)
            milestone_importer = MilestoneImporter(self.service, verbose, stop_on_error)
            epic_importer = EpicImporter(self.service, verbose, stop_on_error)
            # 添加任务导入器初始化
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
                    print(colorize(f"检测到Epic结构，优先导入Epic-Story-Task", "cyan"))
                # Epic导入器会自动导入其下的stories和tasks
                epic_importer.import_epics(yaml_data, roadmap_id, import_stats)

            # 导入里程碑（如果有）
            elif "milestones" in yaml_data:
                logger.info(f"检测到Milestone结构，导入Milestone-Task")
                if verbose:
                    print(colorize(f"检测到Milestone结构，导入Milestone-Task", "cyan"))
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
                    print(colorize(f"仅检测到根级任务，直接导入Task", "cyan"))
                task_importer.import_tasks(yaml_data["tasks"], None, roadmap_id, import_stats)

            # 生成导入结果
            result = self._generate_import_result(file_path, roadmap_id, import_stats, verbose)

            # 如果使用了临时文件，添加相关信息
            if source_file != file_path:
                result["fixed_file"] = source_file
                result["original_file"] = file_path

            return result

        except Exception as e:
            error_msg = f"从YAML导入路线图失败"
            logger.error(f"{error_msg}: {str(e)}")
            print_error(error_msg, e, show_traceback=verbose)
            return {"success": False, "error": f"{error_msg}: {str(e)}"}

    def _validate_and_fix_yaml(self, file_path: str, verbose: bool, force_llm: bool = False) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        验证并修复YAML文件

        该方法委托给RoadmapProcessor处理所有的解析和验证工作。

        Args:
            file_path: YAML文件路径
            verbose: 是否启用详细日志
            force_llm: 是否强制使用LLM解析，不进行其他尝试

        Returns:
            Tuple[str, Optional[Dict[str, Any]]]: (使用的文件路径, YAML数据)
        """
        # 确保文件存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return file_path, None

        try:
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 委托给RoadmapProcessor处理所有解析和验证工作
            from src.parsing.processors.roadmap_processor import RoadmapProcessor

            processor = RoadmapProcessor()

            # 记录解析开始
            if force_llm:
                logger.info(f"开始使用RoadmapProcessor强制LLM解析文件: {file_path}")
                if verbose:
                    print(colorize(f"开始强制LLM解析文件: {file_path}", "cyan"))
            else:
                logger.info(f"开始使用RoadmapProcessor解析文件: {file_path}")
                if verbose:
                    print(colorize(f"开始解析文件: {file_path}", "cyan"))

            # 使用parse_roadmap方法处理YAML内容
            processed_data = processor.parse_roadmap(content)

            if not processed_data or not isinstance(processed_data, dict):
                logger.error("RoadmapProcessor返回的数据无效或不是字典类型")
                if verbose:
                    print(colorize("❌ 解析失败: 返回了无效数据", "red"))
                return file_path, None

            # 创建临时文件存储处理后的数据
            temp_dir = get_temp_dir("roadmap_processed", timestamp_subdir=False)
            temp_filename = f"roadmap_processed_{int(time.time())}_{os.path.basename(file_path)}"
            temp_path = os.path.join(temp_dir, temp_filename)

            try:
                with open(temp_path, "w", encoding="utf-8") as temp_file:
                    yaml.dump(processed_data, temp_file, default_flow_style=False, allow_unicode=True, sort_keys=False)

                logger.info(f"已将处理后的数据保存到: {temp_path}")
                if verbose:
                    print(colorize(f"✅ 已将处理后的数据保存到: {temp_path}", "green"))

                return temp_path, processed_data
            except Exception as e:
                logger.error(f"保存处理后的数据失败: {str(e)}")
                if verbose:
                    print(colorize(f"❌ 保存处理后的数据失败: {str(e)}", "red"))
                if os.path.exists(temp_path):
                    os.unlink(temp_path)  # 删除临时文件
                return file_path, processed_data

        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            if verbose:
                print(colorize(f"❌ 处理文件失败: {str(e)}", "red"))
            return file_path, None

    def _read_yaml_file(self, file_path: str, verbose: bool, force_llm: bool = False) -> Optional[Dict[str, Any]]:
        """
        读取YAML文件内容

        现在仅负责文件读取，解析工作完全委托给_validate_and_fix_yaml

        Args:
            file_path: 文件路径
            verbose: 是否启用详细日志
            force_llm: 是否强制使用LLM解析

        Returns:
            Optional[Dict[str, Any]]: 解析后的数据，解析失败返回None
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                logger.error(error_msg)
                if verbose:
                    print(colorize(error_msg, "red"))
                return None

            # 调用_validate_and_fix_yaml处理文件，传递force_llm参数
            _, yaml_data = self._validate_and_fix_yaml(file_path, verbose, force_llm)
            return yaml_data

        except Exception as e:
            error_msg = f"读取文件失败: {file_path}"
            logger.error(f"{error_msg}: {str(e)}")
            if verbose:
                print(colorize(f"{error_msg}: {str(e)}", "red"))
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
            print(f"\n{colorize('⚠️ 警告', 'yellow', 'bold')}: {colorize('部分项目导入失败，但因为处于详细模式，仍然继续导入', 'yellow')}")

        # 打印导入统计信息
        self._print_import_stats(import_stats)

        return result

    def _print_import_stats(self, import_stats: Dict[str, Dict[str, int]]) -> None:
        """打印导入统计信息"""
        print(f"\n{colorize('📊 导入统计:', 'blue', 'bold')}")
        print(
            f"{colorize('•', 'green')} 里程碑: {colorize(str(import_stats['milestones']['success']), 'green')}成功, {colorize(str(import_stats['milestones']['failed']), 'red' if import_stats['milestones']['failed'] > 0 else 'green')}失败"
        )
        print(
            f"{colorize('•', 'green')} 史诗: {colorize(str(import_stats['epics']['success']), 'green')}成功, {colorize(str(import_stats['epics']['failed']), 'red' if import_stats['epics']['failed'] > 0 else 'green')}失败"
        )
        print(
            f"{colorize('•', 'green')} 故事: {colorize(str(import_stats['stories']['success']), 'green')}成功, {colorize(str(import_stats['stories']['failed']), 'red' if import_stats['stories']['failed'] > 0 else 'green')}失败"
        )
        print(
            f"{colorize('•', 'green')} 任务: {colorize(str(import_stats['tasks']['success']), 'green')}成功, {colorize(str(import_stats['tasks']['failed']), 'red' if import_stats['tasks']['failed'] > 0 else 'green')}失败"
        )
