"""
路线图YAML验证器核心模块

提供路线图YAML文件的主要验证逻辑
"""

import copy
import logging
import os
from typing import Any, Dict, List, Tuple

import yaml

from src.roadmap.sync.yaml_validator_schema import (
    EPIC_FIELDS,
    MILESTONE_FIELDS,
    ROADMAP_FIELDS,
    STORY_FIELDS,
    TASK_FIELDS,
)
from src.roadmap.sync.yaml_validator_section import SectionValidator
from src.roadmap.sync.yaml_validator_template import TemplateManager

logger = logging.getLogger(__name__)


class RoadmapValidator:
    """路线图验证器核心"""

    def __init__(self, template_manager: TemplateManager):
        """
        初始化路线图验证器

        Args:
            template_manager: 模板管理器
        """
        self.template_manager = template_manager

    def validate_yaml(self, yaml_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证YAML文件格式

        Args:
            yaml_path: YAML文件路径

        Returns:
            Tuple[bool, List[str], Dict[str, Any]]:
                - 是否有效
                - 错误/警告消息列表
                - 验证后的数据（可能包含自动修复）
        """
        messages = []

        try:
            # 读取YAML文件
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                messages.append("❌ 错误: YAML文件为空或格式无效")
                # 返回默认模板数据作为修复建议
                return False, messages, copy.deepcopy(self.template_manager.get_template())

            # 验证路线图数据
            is_valid, roadmap_messages, fixed_data = self._validate_roadmap_data(data)
            messages.extend(roadmap_messages)

            return is_valid, messages, fixed_data

        except yaml.YAMLError as e:
            messages.append(f"❌ 错误: YAML格式错误 - {str(e)}")
            return False, messages, copy.deepcopy(self.template_manager.get_template())
        except Exception as e:
            messages.append(f"❌ 错误: 验证过程异常 - {str(e)}")
            return False, messages, copy.deepcopy(self.template_manager.get_template())

    def _validate_roadmap_data(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证路线图数据并尝试修复

        Args:
            data: 路线图数据

        Returns:
            Tuple[bool, List[str], Dict[str, Any]]:
                - 是否有效
                - 错误/警告消息列表
                - 修复后的数据
        """
        messages = []
        is_valid = True
        fixed_data = copy.deepcopy(data)
        template_data = self.template_manager.get_template()

        # 确保data是字典类型
        if not isinstance(data, dict):
            messages.append(f"❌ 错误: YAML根元素不是有效的字典，而是 {type(data)}")
            return False, messages, copy.deepcopy(template_data)

        # 验证必填字段
        for field in ROADMAP_FIELDS["required"]:
            if field not in data:
                is_valid = False
                messages.append(f"❌ 错误: 缺少必填字段 '{field}'")
                # 从模板中填充
                if template_data and field in template_data:
                    fixed_data[field] = template_data[field]
                    messages.append(f"🔧 修复: 已从模板添加 '{field}' 字段")

        # 验证可选字段，提示建议
        for field in ROADMAP_FIELDS["optional"]:
            if field not in data:
                messages.append(f"⚠️ 警告: 缺少可选字段 '{field}'")
                # 从模板中填充
                if template_data and field in template_data:
                    fixed_data[field] = template_data[field]
                    messages.append(f"🔧 修复: 已从模板添加 '{field}' 字段")

        # 验证各部分
        fixed_data = self._validate_milestone_section(
            data, fixed_data, template_data, messages, is_valid
        )
        fixed_data = self._validate_epic_section(
            data, fixed_data, template_data, messages, is_valid
        )
        fixed_data = self._validate_story_section(
            data, fixed_data, template_data, messages, is_valid
        )
        fixed_data = self._validate_task_section(
            data, fixed_data, template_data, messages, is_valid
        )

        # 重新评估是否有效
        is_valid = not any(msg.startswith("❌ 错误") for msg in messages)

        return is_valid, messages, fixed_data

    def _validate_milestone_section(
        self,
        data: Dict[str, Any],
        fixed_data: Dict[str, Any],
        template_data: Dict[str, Any],
        messages: List[str],
        is_valid: bool,
    ) -> Dict[str, Any]:
        """验证里程碑部分"""
        if "milestones" not in data:
            messages.append("⚠️ 警告: 路线图没有里程碑字段")
            fixed_data["milestones"] = template_data.get("milestones", [])
            messages.append("🔧 修复: 已添加里程碑字段")
        elif not isinstance(data["milestones"], list):
            messages.append(f"❌ 错误: 里程碑字段不是列表类型，而是 {type(data['milestones'])}")
            fixed_data["milestones"] = template_data.get("milestones", [])
            messages.append("🔧 修复: 已修复里程碑字段类型")
        elif not data["milestones"]:
            messages.append("⚠️ 警告: 路线图里程碑列表为空")
            fixed_data["milestones"] = template_data.get("milestones", [])
            messages.append("🔧 修复: 已从模板添加示例里程碑")
        else:
            fixed_milestones = []
            for i, milestone in enumerate(data["milestones"]):
                if milestone is None:
                    messages.append(f"❌ 错误: 里程碑 #{i+1} 是空值")
                    continue

                if not isinstance(milestone, dict):
                    messages.append(f"❌ 错误: 里程碑 #{i+1} 不是字典类型，而是 {type(milestone)}")
                    continue

                (
                    milestone_valid,
                    milestone_msgs,
                    fixed_milestone,
                ) = SectionValidator.validate_section(milestone, "milestone", MILESTONE_FIELDS, i)
                if not milestone_valid:
                    is_valid = False
                messages.extend(milestone_msgs)
                fixed_milestones.append(fixed_milestone)

            if fixed_milestones:
                fixed_data["milestones"] = fixed_milestones
            else:
                fixed_data["milestones"] = template_data.get("milestones", [])
                messages.append("🔧 修复: 由于验证失败，已从模板添加示例里程碑")

        return fixed_data

    def _validate_epic_section(
        self,
        data: Dict[str, Any],
        fixed_data: Dict[str, Any],
        template_data: Dict[str, Any],
        messages: List[str],
        is_valid: bool,
    ) -> Dict[str, Any]:
        """验证史诗部分"""
        if "epics" not in data:
            messages.append("⚠️ 警告: 路线图没有史诗字段")
            fixed_data["epics"] = template_data.get("epics", [])
            messages.append("🔧 修复: 已添加史诗字段")
        elif not isinstance(data["epics"], list):
            messages.append(f"❌ 错误: 史诗字段不是列表类型，而是 {type(data['epics'])}")
            fixed_data["epics"] = template_data.get("epics", [])
            messages.append("🔧 修复: 已修复史诗字段类型")
        elif not data["epics"]:
            messages.append("⚠️ 警告: 路线图史诗列表为空")
            fixed_data["epics"] = template_data.get("epics", [])
            messages.append("🔧 修复: 已从模板添加示例史诗")
        else:
            fixed_epics = []
            for i, epic in enumerate(data["epics"]):
                if epic is None:
                    messages.append(f"❌ 错误: 史诗 #{i+1} 是空值")
                    continue

                if not isinstance(epic, dict):
                    messages.append(f"❌ 错误: 史诗 #{i+1} 不是字典类型，而是 {type(epic)}")
                    continue

                epic_valid, epic_msgs, fixed_epic = SectionValidator.validate_section(
                    epic, "epic", EPIC_FIELDS, i
                )
                if not epic_valid:
                    is_valid = False
                messages.extend(epic_msgs)
                fixed_epics.append(fixed_epic)

            if fixed_epics:
                fixed_data["epics"] = fixed_epics
            else:
                fixed_data["epics"] = template_data.get("epics", [])
                messages.append("🔧 修复: 由于验证失败，已从模板添加示例史诗")

        return fixed_data

    def _validate_story_section(
        self,
        data: Dict[str, Any],
        fixed_data: Dict[str, Any],
        template_data: Dict[str, Any],
        messages: List[str],
        is_valid: bool,
    ) -> Dict[str, Any]:
        """验证用户故事部分"""
        if "stories" not in data:
            messages.append("ℹ️ 提示: 路线图没有用户故事字段")
            fixed_data["stories"] = []
            messages.append("🔧 修复: 已添加空的用户故事字段")
        elif not isinstance(data["stories"], list):
            messages.append(f"❌ 错误: 用户故事字段不是列表类型，而是 {type(data['stories'])}")
            fixed_data["stories"] = []
            messages.append("🔧 修复: 已修复用户故事字段类型")
        elif not data["stories"]:
            messages.append("ℹ️ 提示: 路线图用户故事列表为空")
            fixed_data["stories"] = []
        else:
            fixed_stories = []
            for i, story in enumerate(data["stories"]):
                if story is None:
                    messages.append(f"❌ 错误: 用户故事 #{i+1} 是空值")
                    continue

                if not isinstance(story, dict):
                    messages.append(f"❌ 错误: 用户故事 #{i+1} 不是字典类型，而是 {type(story)}")
                    continue

                story_valid, story_msgs, fixed_story = SectionValidator.validate_section(
                    story, "story", STORY_FIELDS, i
                )
                if not story_valid:
                    is_valid = False
                messages.extend(story_msgs)
                fixed_stories.append(fixed_story)

            fixed_data["stories"] = fixed_stories

        return fixed_data

    def _validate_task_section(
        self,
        data: Dict[str, Any],
        fixed_data: Dict[str, Any],
        template_data: Dict[str, Any],
        messages: List[str],
        is_valid: bool,
    ) -> Dict[str, Any]:
        """验证任务部分"""
        if "tasks" not in data:
            messages.append("ℹ️ 提示: 路线图没有任务字段")
            fixed_data["tasks"] = []
            messages.append("🔧 修复: 已添加空的任务字段")
        elif not isinstance(data["tasks"], list):
            messages.append(f"❌ 错误: 任务字段不是列表类型，而是 {type(data['tasks'])}")
            fixed_data["tasks"] = []
            messages.append("🔧 修复: 已修复任务字段类型")
        elif not data["tasks"]:
            messages.append("ℹ️ 提示: 路线图任务列表为空")
            fixed_data["tasks"] = []
        else:
            fixed_tasks = []
            for i, task in enumerate(data["tasks"]):
                if task is None:
                    messages.append(f"❌ 错误: 任务 #{i+1} 是空值")
                    continue

                if not isinstance(task, dict):
                    messages.append(f"❌ 错误: 任务 #{i+1} 不是字典类型，而是 {type(task)}")
                    continue

                task_valid, task_msgs, fixed_task = SectionValidator.validate_section(
                    task, "task", TASK_FIELDS, i
                )
                if not task_valid:
                    is_valid = False
                messages.extend(task_msgs)
                fixed_tasks.append(fixed_task)

            fixed_data["tasks"] = fixed_tasks

        return fixed_data
