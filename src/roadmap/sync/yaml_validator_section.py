"""
路线图YAML验证器部分验证模块

负责验证路线图各部分（里程碑、史诗、故事、任务）的格式
"""

import copy
import logging
from typing import Any, Dict, List, Tuple

from src.roadmap.sync.yaml_validator_schema import SECTION_NAMES, VALID_PRIORITY, VALID_STATUS

logger = logging.getLogger(__name__)


class SectionValidator:
    """路线图部分验证器"""

    @staticmethod
    def validate_section(
        section: Dict[str, Any], section_type: str, fields: Dict[str, List[str]], index: int
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        验证路线图的一个部分（里程碑、史诗等）

        Args:
            section: 部分数据
            section_type: 部分类型（milestone, epic, story, task）
            fields: 字段定义
            index: 当前项索引

        Returns:
            Tuple[bool, List[str], Dict[str, Any]]:
                - 是否有效
                - 错误/警告消息列表
                - 修复后的数据
        """
        messages = []
        is_valid = True
        fixed_section = copy.deepcopy(section)

        # 验证必填字段
        for field in fields["required"]:
            if field not in section:
                is_valid = False
                messages.append(f"❌ 错误: {section_type} #{index+1} 缺少必填字段 '{field}'")
                # 添加默认值
                if field == "title":
                    fixed_section[field] = f"示例{SectionValidator.get_section_name(section_type)}"
                    messages.append(f"🔧 修复: 已添加默认标题 '{fixed_section[field]}'")
                elif field == "description":
                    fixed_section[
                        field
                    ] = f"这是一个示例{SectionValidator.get_section_name(section_type)}"
                    messages.append(f"🔧 修复: 已添加默认描述")

        # 验证状态字段
        if "status" in section and section_type in VALID_STATUS:
            if section["status"] not in VALID_STATUS[section_type]:
                messages.append(
                    f"⚠️ 警告: {section_type} #{index+1} 状态 '{section['status']}' 无效，"
                    f"有效值: {', '.join(VALID_STATUS[section_type])}"
                )
                fixed_section["status"] = VALID_STATUS[section_type][0]
                messages.append(f"🔧 修复: 已将状态设置为 '{VALID_STATUS[section_type][0]}'")

        # 验证优先级（仅任务）
        if section_type == "task" and "priority" in section:
            if section["priority"] not in VALID_PRIORITY:
                messages.append(
                    f"⚠️ 警告: 任务 #{index+1} 优先级 '{section['priority']}' 无效，"
                    f"有效值: {', '.join(VALID_PRIORITY)}"
                )
                fixed_section["priority"] = "P2"
                messages.append(f"🔧 修复: 已将优先级设置为 'P2'")

        # 验证进度百分比
        if "progress" in section:
            try:
                progress = int(section["progress"])
                if progress < 0 or progress > 100:
                    messages.append(f"⚠️ 警告: {section_type} #{index+1} 进度 {progress} 超出范围 (0-100)")
                    fixed_section["progress"] = max(0, min(100, progress))
                    messages.append(f"🔧 修复: 已将进度调整为 {fixed_section['progress']}")
            except (ValueError, TypeError):
                messages.append(
                    f"⚠️ 警告: {section_type} #{index+1} 进度值 '{section['progress']}' 不是有效数字"
                )
                fixed_section["progress"] = 0
                messages.append(f"🔧 修复: 已将进度设置为 0")

        return is_valid, messages, fixed_section

    @staticmethod
    def get_section_name(section_type: str) -> str:
        """
        获取部分的中文名称

        Args:
            section_type: 部分类型

        Returns:
            str: 中文名称
        """
        return SECTION_NAMES.get(section_type, section_type)
