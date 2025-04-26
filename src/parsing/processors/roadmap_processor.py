"""
路线图处理器

用于路线图数据的智能解析和结构转换，主要功能包括：
1. 将不规范的YAML转换为正确的路线图结构
2. 将milestone格式转换为epic-story-task结构
3. 修复常见的结构问题
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import yaml

from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)

# 定义项目根目录和临时目录常量 - No longer needed
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
# TEMP_ROOT = os.path.join(PROJECT_ROOT, "temp")


class RoadmapProcessor:
    """路线图数据处理器 - 只进行标准YAML解析和验证"""

    def __init__(self):
        """初始化路线图处理器"""
        # Remove LLM service initialization
        # config = {"provider": "openai", "format": "yaml", "content_type": "roadmap"}
        # self.llm_service = create_llm_service("openai", config)

        # 初始化验证器
        try:
            self.validator = RoadmapValidator()
        except Exception as e:
            logger.warning(f"初始化验证器失败: {str(e)}，将使用None")
            self.validator = None

        # Keep these maps for potential future use or validation
        self.priority_map = {
            "P0": "critical",
            "P1": "high",
            "P2": "medium",
            "P3": "low",
            "highest": "critical",
            "higher": "high",
            "normal": "medium",
            "lower": "low",
            "lowest": "low",
        }

        # 时间戳目录，用于临时文件
        self._timestamp_dir = None

    async def parse_roadmap(self, content: str) -> Optional[Dict[str, Any]]:
        """使用 PyYAML 解析路线图内容，并进行验证。"""
        logger.info("🚀 开始使用 PyYAML 解析路线图...")

        try:
            # 1. 使用 yaml.safe_load 解析
            data = yaml.safe_load(content)
            logger.info("✅ YAML 解析成功。")

            # 2. 检查解析结果是否为字典
            if not isinstance(data, dict):
                logger.error("❌ YAML 文件内容不是有效的字典结构。")
                return None  # Return None on parsing failure

            # 3. (可选) 验证解析后的数据结构
            if self.validator:
                is_valid = self.validator.validate(data)
                if is_valid:
                    logger.info("✅ 解析结果通过结构验证。")
                else:
                    errors = self.validator.get_errors()
                    warnings = self.validator.get_warnings()
                    logger.warning(f"⚠️ YAML解析成功但验证失败: {errors}")
                    # Decide whether to return data despite validation errors
                    # For strict mode, return None:
                    # return None
                    # For lenient mode (allow import with warnings):
                    # Add warnings to data? For now, just log and return data.
                    pass  # Logged warning, proceed with potentially invalid data
            else:
                logger.warning("⚠️ 验证器未初始化，跳过结构验证。")

            # 4. (可选) 运行修复/规范化逻辑（如果需要，但现在不依赖LLM）
            # data = self.fix_field_mapping(data)
            # data = self.fix_priority_format(data)
            # data = self.fix_empty_status(data)
            # logger.info("⚙️ 已应用本地修复规则（如果适用）。")

            # 5. 返回解析（并可能验证/修复）的数据
            return data

        except yaml.YAMLError as e:
            logger.error(f"❌ YAML 解析错误: {e}", exc_info=True)
            return None  # Return None on YAMLError
        except Exception as e:
            logger.error(f"❌ 处理路线图内容时发生意外错误: {e}", exc_info=True)
            return None  # Return None on other exceptions

    def fix_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复字段映射，处理不同命名规范之间的转换"""
        # 字段名称映射表
        field_map = {"name": "title", "desc": "description", "description": "description", "owner": "assignee", "priority": "priority"}

        # 如果有epics字段，处理每个epic
        if "epics" in data and isinstance(data["epics"], list):
            for epic in data["epics"]:
                # 处理epic的字段映射
                for old_field, new_field in field_map.items():
                    if old_field in epic and old_field != new_field:
                        epic[new_field] = epic.pop(old_field)

                # 如果有stories字段，处理每个story
                if "stories" in epic and isinstance(epic["stories"], list):
                    for story in epic["stories"]:
                        # 处理story的字段映射
                        for old_field, new_field in field_map.items():
                            if old_field in story and old_field != new_field:
                                story[new_field] = story.pop(old_field)

                        # 如果有tasks字段，处理每个task
                        if "tasks" in story and isinstance(story["tasks"], list):
                            for task in story["tasks"]:
                                # 处理task的字段映射
                                for old_field, new_field in field_map.items():
                                    if old_field in task and old_field != new_field:
                                        task[new_field] = task.pop(old_field)

        return data

    def fix_empty_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复空数组和状态值问题"""
        if "epics" not in data or not data["epics"]:
            # 如果epics为空或不存在，添加一个默认的epic
            data["epics"] = [{"title": "默认功能模块", "description": "自动创建的功能模块", "stories": []}]
            logger.warning("⚠️ 添加默认epic，因为epics数组为空")

        for epic_index, epic in enumerate(data["epics"]):
            # 确保epic有stories字段且不为空
            if "stories" not in epic or not epic["stories"]:
                epic["stories"] = [{"title": f"{epic.get('title', '模块')}的默认故事", "status": "planned", "priority": "medium", "tasks": []}]
                logger.warning(f"⚠️ 为Epic #{epic_index+1} '{epic.get('title', '未命名')}' 添加默认story")

            for story_index, story in enumerate(epic["stories"]):
                # 确保story有tasks字段且不为空
                if "tasks" not in story or not story["tasks"]:
                    story["tasks"] = [{"title": f"{story.get('title', '故事')}的默认任务", "status": "todo"}]
                    logger.warning(f"⚠️ 为Story #{story_index+1} '{story.get('title', '未命名')}' 添加默认task")

                for task in story["tasks"]:
                    # 确保task有status字段且值有效
                    if "status" not in task or task["status"] == "" or task["status"] not in ["todo", "in_progress", "done", "completed"]:
                        task["status"] = "todo"
                        logger.warning(f"⚠️ 修复task '{task.get('title', '未命名')}' 的status值为'todo'")

                    # 确保task有title字段
                    if "title" not in task or not task["title"]:
                        task["title"] = "自动创建的任务"
                        logger.warning("⚠️ 为task添加默认title")

        return data

    def fix_priority_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修复优先级格式，将P0/P1/P2格式转换为low/medium/high/critical"""
        # 如果有epics字段，处理每个epic
        if "epics" in data and isinstance(data["epics"], list):
            for epic in data["epics"]:
                # 处理epic的优先级
                if "priority" in epic and epic["priority"] in self.priority_map:
                    epic["priority"] = self.priority_map[epic["priority"]]

                # 如果有stories字段，处理每个story
                if "stories" in epic and isinstance(epic["stories"], list):
                    for story in epic["stories"]:
                        # 处理story的优先级
                        if "priority" in story and story["priority"] in self.priority_map:
                            story["priority"] = self.priority_map[story["priority"]]

                        # 如果有tasks字段，处理每个task
                        if "tasks" in story and isinstance(story["tasks"], list):
                            for task in story["tasks"]:
                                # 处理task的优先级
                                if "priority" in task and task["priority"] in self.priority_map:
                                    task["priority"] = self.priority_map[task["priority"]]

        return data


# 导出类
__all__ = ["RoadmapProcessor"]
