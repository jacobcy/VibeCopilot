"""
路线图验证模块

提供路线图数据结构验证和错误报告功能。
强制要求使用新格式（Epic -> Story -> Task），不再支持旧格式（Milestone -> Task）。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from src.validation.core.roadmap_validator import RoadmapCoreValidator
from src.validation.schema.roadmap_schema import get_roadmap_schema

logger = logging.getLogger(__name__)


class RoadmapValidator:
    """
    路线图验证器，验证路线图数据是否符合指定的结构标准

    要求路线图必须使用完整的epic-story-task结构：
    - 必须包含epics数组
    - 每个epic必须包含stories数组
    - 每个story必须包含tasks数组
    - 不支持只使用milestones或根级tasks的结构
    """

    def __init__(self):
        """初始化路线图验证器"""
        self.schema = get_roadmap_schema()
        self.core_validator = RoadmapCoreValidator(self.schema)
        self.warnings = []
        self.errors = []

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证路线图数据是否符合模式规范

        要求必须使用完整的epic-story-task结构，不支持旧的milestones-task结构。

        Args:
            data: 待验证的路线图数据

        Returns:
            bool: 验证是否通过
        """
        # 重置警告和错误信息
        self.warnings = []
        self.errors = []

        # 基本结构检查
        if not isinstance(data, dict):
            self.errors.append("路线图数据必须是字典格式")
            return False

        # 检查metadata部分
        if "metadata" not in data:
            self.warnings.append("缺少metadata部分，将使用默认值")
        elif not isinstance(data["metadata"], dict):
            self.errors.append("metadata必须是字典格式")
            return False

        # 检查epics数组
        if "epics" not in data:
            self.errors.append("路线图必须包含epics数组")
            return False

        if not isinstance(data["epics"], list):
            self.errors.append("epics必须是数组格式")
            return False

        # 检查每个epic
        for i, epic in enumerate(data.get("epics", [])):
            if not isinstance(epic, dict):
                self.errors.append(f"第{i+1}个epic必须是字典格式")
                continue

            # 检查epic必需字段
            if "title" not in epic:
                self.errors.append(f"第{i+1}个epic缺少title字段")

            # 检查stories数组
            if "stories" not in epic:
                self.errors.append(f"第{i+1}个epic缺少stories数组")
                continue

            if not isinstance(epic["stories"], list):
                self.errors.append(f"第{i+1}个epic的stories必须是数组格式")
                continue

            # 检查每个story
            for j, story in enumerate(epic.get("stories", [])):
                if not isinstance(story, dict):
                    self.errors.append(f"第{i+1}个epic的第{j+1}个story必须是字典格式")
                    continue

                # 检查story必需字段
                if "title" not in story:
                    self.errors.append(f"第{i+1}个epic的第{j+1}个story缺少title字段")

                # 检查tasks数组
                if "tasks" not in story:
                    self.warnings.append(f"第{i+1}个epic的第{j+1}个story缺少tasks数组")
                    continue

                if not isinstance(story.get("tasks", []), list):
                    self.errors.append(f"第{i+1}个epic的第{j+1}个story的tasks必须是数组格式")
                    continue

        # 检查故事状态是否在允许的范围内
        valid_status = ["draft", "planned", "in_progress", "completed", "todo", "doing", "done", "backlog"]
        for i, epic in enumerate(data.get("epics", [])):
            for j, story in enumerate(epic.get("stories", [])):
                status = story.get("status")
                if status and status.lower() not in valid_status:
                    self.warnings.append(f"第{i+1}个epic的第{j+1}个story使用了非标准状态值: {status}")
                    # 建议修正
                    story["status"] = self._map_status(status)

        # 使用核心验证器进行详细验证
        is_valid = len(self.errors) == 0 and self.core_validator.validate(data)

        # 合并核心验证器的警告和错误
        self.warnings.extend(self.core_validator.get_warnings())
        self.errors.extend(self.core_validator.get_errors())

        return is_valid

    def validate_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        验证YAML文件中的路线图数据

        Args:
            file_path: YAML文件路径

        Returns:
            Tuple[bool, List[str], List[str]]: (验证是否通过, 警告列表, 错误列表)
        """
        logger.info(f"开始验证路线图文件: {file_path}")

        # 重置警告和错误信息
        self.warnings = []
        self.errors = []

        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.errors.append(f"文件不存在: {file_path}")
            return False, [], self.errors

        # 读取并解析YAML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML解析错误: {str(e)}")
            return False, [], self.errors
        except Exception as e:
            self.errors.append(f"文件读取错误: {str(e)}")
            return False, [], self.errors

        # 验证数据
        is_valid = self.validate(data)

        if is_valid:
            logger.info("文件验证通过")
        else:
            logger.warning(f"文件验证失败: {len(self.errors)}个错误, {len(self.warnings)}个警告")

        return is_valid, self.warnings, self.errors

    def get_warnings(self) -> List[str]:
        """获取验证警告信息"""
        return self.warnings

    def get_errors(self) -> List[str]:
        """获取验证错误信息"""
        return self.errors

    def _map_status(self, status: str) -> str:
        """将非标准状态映射到标准状态"""
        status = status.lower()

        # 状态映射表
        status_map = {
            # 中文状态映射
            "未开始": "draft",
            "已计划": "planned",
            "进行中": "in_progress",
            "已完成": "completed",
            "待办": "todo",
            "进行": "doing",
            "完成": "done",
            "待定": "backlog",
            "默认状态": "draft",
            # 英文别名映射
            "new": "draft",
            "pending": "planned",
            "wip": "in_progress",
            "finished": "completed",
            "complete": "completed",
            "ready": "planned",
            "review": "in_progress",
            "testing": "in_progress",
            "todo": "draft",
        }

        return status_map.get(status, "draft")
