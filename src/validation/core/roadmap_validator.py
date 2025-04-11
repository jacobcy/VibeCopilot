"""
路线图核心验证器

提供路线图数据的核心验证功能，专注于验证epic-story-task结构。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from jsonschema import Draft7Validator, ValidationError

from src.validation.core.validator import Validator

logger = logging.getLogger(__name__)


class RoadmapCoreValidator(Validator):
    """路线图核心验证器"""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        初始化路线图验证器

        Args:
            schema: 可选的JSON Schema定义
        """
        super().__init__()
        self.schema = schema

        if self.schema:
            self.validator = Draft7Validator(self.schema)
        else:
            self.validator = None

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证路线图数据

        Args:
            data: 路线图数据

        Returns:
            bool: 验证是否通过
        """
        # 清空之前的验证结果
        self.clear_messages()

        # 基本结构验证 - 确保有epic-story-task结构
        is_valid = self._validate_basic_structure(data)
        if not is_valid:
            return False

        # 如果有schema，进行schema验证
        if self.validator:
            schema_valid = self._validate_schema(data)
            is_valid = is_valid and schema_valid
            if not is_valid:
                return False

        # 验证epic-story-task结构的完整性
        self._validate_structure(data)

        # 验证结果：结构有效且没有错误
        return is_valid and not self.errors

    def _validate_basic_structure(self, data: Dict[str, Any]) -> bool:
        """
        验证基本数据结构

        Args:
            data: 路线图数据

        Returns:
            bool: 基本结构是否有效
        """
        if not isinstance(data, dict):
            self.errors.append("数据必须是字典类型")
            return False

        # 检查metadata
        if "metadata" not in data:
            self.warnings.append("缺少metadata部分")
        elif not isinstance(data["metadata"], dict):
            self.errors.append("metadata必须是字典类型")
            return False

        # 必须有epics结构
        if "epics" not in data:
            self.errors.append("缺少epics部分，必须使用epic-story-task结构")
            return False

        if not isinstance(data["epics"], list):
            self.errors.append("epics必须是列表类型")
            return False

        # 检查epics是否为空
        if len(data["epics"]) == 0:
            self.errors.append("epics不能为空")
            return False

        # 检查milestones
        if "milestones" in data:
            if not isinstance(data["milestones"], list):
                self.errors.append("milestones必须是列表类型")
                return False

        # 检查根级tasks - 不允许只有根级tasks
        if "tasks" in data and "epics" not in data:
            self.errors.append("不允许只使用根级tasks，必须使用epic-story-task结构")
            return False

        return True

    def _validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        使用JSON Schema验证数据

        Args:
            data: 路线图数据

        Returns:
            bool: Schema验证是否通过
        """
        if not self.validator:
            return True

        try:
            errors = list(self.validator.iter_errors(data))
            if errors:
                for error in errors:
                    path = ".".join(str(p) for p in error.path) if error.path else "根节点"
                    self.errors.append(f"Schema验证错误 - 路径: '{path}', 问题: {error.message}")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Schema验证异常: {str(e)}")
            return False

    def _validate_structure(self, data: Dict[str, Any]) -> None:
        """
        验证epic-story-task结构

        Args:
            data: 路线图数据
        """
        # 检查epics结构
        if "epics" in data and isinstance(data["epics"], list):
            if len(data["epics"]) == 0:
                self.errors.append("epics不能为空列表")

            for i, epic in enumerate(data["epics"]):
                self._validate_epic(epic, i)

        # 检查是否使用了旧的结构，强制使用epic-story-task结构
        if "milestones" in data and not "epics" in data:
            self.errors.append("不允许使用旧的milestones结构，必须使用epic-story-task结构")

        if "tasks" in data and not "epics" in data:
            self.errors.append("不允许使用根级tasks，必须使用epic-story-task结构")

    def _validate_epic(self, epic: Dict[str, Any], index: int) -> None:
        """
        验证单个epic的结构

        Args:
            epic: epic数据
            index: epic索引
        """
        if not isinstance(epic, dict):
            self.errors.append(f"Epic #{index+1} 必须是字典类型")
            return

        # 检查必填字段
        if "title" not in epic or not epic["title"]:
            self.errors.append(f"Epic #{index+1} 缺少title字段")

        # 检查stories
        if "stories" not in epic:
            self.errors.append(f"Epic #{index+1} '{epic.get('title', '未命名')}' 缺少stories字段")
        elif not isinstance(epic["stories"], list):
            self.errors.append(f"Epic #{index+1} '{epic.get('title', '未命名')}' 的stories必须是列表类型")
        elif len(epic["stories"]) == 0:
            self.errors.append(f"Epic #{index+1} '{epic.get('title', '未命名')}' 的stories不能为空")
        else:
            # 验证每个story
            for j, story in enumerate(epic["stories"]):
                self._validate_story(story, index, j)

    def _validate_story(self, story: Dict[str, Any], epic_index: int, story_index: int) -> None:
        """
        验证单个story的结构

        Args:
            story: story数据
            epic_index: 所属epic的索引
            story_index: story索引
        """
        if not isinstance(story, dict):
            self.errors.append(f"Epic #{epic_index+1} 的 Story #{story_index+1} 必须是字典类型")
            return

        # 检查必填字段
        if "title" not in story or not story["title"]:
            self.errors.append(f"Epic #{epic_index+1} 的 Story #{story_index+1} 缺少title字段")

        # 检查tasks
        if "tasks" not in story:
            self.errors.append(f"Story #{story_index+1} '{story.get('title', '未命名')}' 在 Epic #{epic_index+1} 中缺少tasks字段")
        elif not isinstance(story["tasks"], list):
            self.errors.append(f"Story #{story_index+1} '{story.get('title', '未命名')}' 在 Epic #{epic_index+1} 中的tasks必须是列表类型")
        elif len(story["tasks"]) == 0:
            self.errors.append(f"Story #{story_index+1} '{story.get('title', '未命名')}' 在 Epic #{epic_index+1} 中的tasks不能为空")
        else:
            # 验证每个task
            for k, task in enumerate(story["tasks"]):
                self._validate_task(task, epic_index, story_index, k)

    def _validate_task(self, task: Dict[str, Any], epic_index: int, story_index: int, task_index: int) -> None:
        """
        验证单个task的结构

        Args:
            task: task数据
            epic_index: 所属epic的索引
            story_index: 所属story的索引
            task_index: task索引
        """
        if not isinstance(task, dict):
            self.errors.append(f"Epic #{epic_index+1} 的 Story #{story_index+1} 的 Task #{task_index+1} 必须是字典类型")
            return

        # 检查必填字段
        if "title" not in task or not task["title"]:
            self.errors.append(f"Epic #{epic_index+1} 的 Story #{story_index+1} 的 Task #{task_index+1} 缺少title字段")

    def validate_file(self, file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        验证路线图YAML文件

        Args:
            file_path: 文件路径

        Returns:
            Tuple[bool, List[str], List[str]]: (验证结果, 警告列表, 错误列表)
        """
        logger.info(f"开始验证文件: {file_path}")

        if not os.path.exists(file_path):
            return False, [], [f"文件不存在: {file_path}"]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"YAML文件为空或格式错误: {file_path}")
                return False, [], [f"YAML文件为空或格式错误: {file_path}"]

            is_valid = self.validate(data)
            logger.info(f"文件验证结果: {is_valid}, 警告: {len(self.warnings)}, 错误: {len(self.errors)}")
            return is_valid, self.warnings, self.errors

        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {str(e)}")
            return False, [], [f"YAML解析错误: {str(e)}"]
        except Exception as e:
            logger.error(f"验证过程中出现异常: {str(e)}")
            return False, [], [f"验证过程中出现异常: {str(e)}"]
