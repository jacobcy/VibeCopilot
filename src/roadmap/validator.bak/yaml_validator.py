"""
路线图YAML验证器

提供用于验证和修复路线图YAML文件格式的核心功能
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from src.parsing.base_parser import BaseParser
from src.parsing.parser_factory import create_parser, get_parser_for_file
from src.roadmap.validator.yaml_validator_schema import ROADMAP_FIELDS, SECTION_FIELDS, SECTION_NAMES, SECTION_NAMES_CH, VALID_PRIORITY, VALID_STATUS
from src.roadmap.validator.yaml_validator_section import SectionValidator

logger = logging.getLogger(__name__)


class RoadmapYamlValidator:
    """路线图YAML验证器类"""

    def __init__(self, template_path: Optional[str] = None):
        """
        初始化验证器

        Args:
            template_path: 自定义模板文件路径
        """
        self.template_path = template_path
        self._template = None

    def validate(self, yaml_file: str) -> Tuple[bool, List[Tuple[str, str]], Optional[Dict[str, Any]]]:
        """
        验证YAML文件格式

        Args:
            yaml_file: YAML文件路径

        Returns:
            Tuple[bool, List[Tuple[str, str]], Optional[Dict]]:
                - 是否有效
                - 消息列表(类型, 消息内容)
                - 修复后的数据(如果可以修复)
        """
        messages = []
        fixed_data = None

        try:
            # 读取YAML文件
            with open(yaml_file, "r", encoding="utf-8") as f:
                raw_content = f.read()

            # 尝试解析YAML
            try:
                data = yaml.safe_load(raw_content)

                if not data:
                    messages.append(("error", f"无法解析YAML文件: {yaml_file}"))
                    # 尝试使用统一解析器
                    fixed_data = self._attempt_parsing(raw_content, yaml_file)
                    if fixed_data:
                        messages.append(("info", "使用解析器成功修复了YAML格式"))
                    else:
                        return False, messages, None
            except yaml.YAMLError as e:
                messages.append(("error", f"YAML格式错误: {str(e)}"))
                # 尝试使用统一解析器
                fixed_data = self._attempt_parsing(raw_content, yaml_file)
                if fixed_data:
                    messages.append(("info", "使用解析器成功修复了YAML格式"))
                    data = fixed_data
                else:
                    return False, messages, None

            # 如果成功解析，继续验证
            if data:
                # 处理元数据顶层键
                if "metadata" not in data and any(key in data for key in ["title", "description", "version"]):
                    metadata = {}
                    for key in ["title", "description", "version", "author", "theme", "last_updated"]:
                        if key in data:
                            metadata[key] = data.pop(key)

                    if metadata:
                        data["metadata"] = metadata
                        fixed_data = data
                        messages.append(("info", "已将顶层元数据字段移动到metadata部分"))

                # 验证基本结构
                is_valid_structure, structure_messages, fixed_structure = self._validate_structure(data)
                messages.extend(structure_messages)

                # 验证各个部分
                if fixed_structure:
                    data = fixed_structure

                is_valid_content, content_messages, fixed_content = self._validate_content(data)
                messages.extend(content_messages)

                # 综合结果
                is_valid = is_valid_structure and is_valid_content

                # 如果有修复，更新数据
                if fixed_content:
                    fixed_data = fixed_content
                elif fixed_structure:
                    fixed_data = fixed_structure

                return is_valid, messages, fixed_data

            return False, messages, fixed_data

        except Exception as e:
            messages.append(("error", f"验证过程中出错: {str(e)}"))
            return False, messages, None

    def _attempt_parsing(self, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        使用解析器尝试解析内容

        Args:
            content: 需要解析的内容
            file_path: 源文件路径

        Returns:
            Optional[Dict[str, Any]]: 解析后的数据，如果失败则为None
        """
        try:
            # 使用文件解析器
            parser = get_parser_for_file(file_path)
            if parser:
                result = parser.parse(content)
                if isinstance(result, dict):
                    return result
                logger.warning(f"解析结果不是字典: {type(result)}")

            # 尝试使用YAML专用解析器
            yaml_parser = create_parser("data", "regex", {"format": "yaml"})
            if yaml_parser:
                result = yaml_parser.parse(content)
                if isinstance(result, dict):
                    return result

            return None
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            return None

    def _validate_structure(self, data: Dict) -> Tuple[bool, List[Tuple[str, str]], Dict]:
        """
        验证YAML文件的基本结构

        Args:
            data: YAML数据

        Returns:
            Tuple[bool, List[Tuple[str, str]], Optional[Dict]]:
                - 是否有效
                - 消息列表
                - 修复后的数据(如果可以修复)
        """
        messages = []
        fixed_data = data.copy()
        is_valid = True

        # 检查必要的顶级部分是否存在
        required_sections = ["metadata", "milestones"]
        missing_sections = [section for section in required_sections if section not in data]

        if missing_sections:
            is_valid = False
            for section in missing_sections:
                messages.append(("error", f"缺少必要的部分: {section}"))
                # 添加默认结构
                if section == "metadata":
                    fixed_data["metadata"] = {"title": "Default Roadmap", "description": "Auto-generated roadmap", "version": "1.0"}
                elif section == "milestones":
                    fixed_data["milestones"] = []

        # 检查至少有一个任务部分
        if "tasks" not in data and "stories" not in data and "epics" not in data:
            messages.append(("warning", "未找到任何任务、故事或史诗部分，路线图可能不完整"))
            fixed_data["tasks"] = []

        # 检查每个部分是否是正确的类型
        for section in data:
            if section in SECTION_NAMES:
                if section == "metadata" and not isinstance(data[section], dict):
                    messages.append(("error", f"部分'{section}'必须是一个字典/映射"))
                    fixed_data[section] = {"title": "Default Roadmap", "description": "Auto-generated roadmap"}
                    is_valid = False
                elif section in ["milestones", "epics", "stories", "tasks", "dependencies"] and not isinstance(data[section], list):
                    messages.append(("error", f"部分'{section}'必须是一个列表"))
                    fixed_data[section] = []
                    is_valid = False

        return is_valid, messages, fixed_data if not is_valid else None

    def _validate_content(self, data: Dict) -> Tuple[bool, List[Tuple[str, str]], Dict]:
        """
        验证YAML文件的内容

        Args:
            data: YAML数据

        Returns:
            Tuple[bool, List[Tuple[str, str]], Optional[Dict]]:
                - 是否有效
                - 消息列表
                - 修复后的数据(如果可以修复)
        """
        messages = []
        fixed_data = data.copy()
        need_fix = False

        # 验证元数据
        if "metadata" in data and isinstance(data["metadata"], dict):
            metadata = fixed_data["metadata"]
            for field in SECTION_FIELDS.get("metadata", {}).get("required", []):
                if field not in metadata or not metadata[field]:
                    messages.append(("error", f"元数据缺少必填字段: {field}"))
                    if field == "title":
                        metadata["title"] = "未命名路线图"
                        need_fix = True
                    elif field == "description":
                        metadata["description"] = "自动生成的路线图描述"
                        need_fix = True

        # 验证里程碑
        if "milestones" in data and isinstance(data["milestones"], list):
            milestones = fixed_data["milestones"]
            for i, milestone in enumerate(milestones):
                if not isinstance(milestone, dict):
                    messages.append(("error", f"里程碑 #{i+1} 不是有效的对象"))
                    continue

                # 检查必填字段
                for field in SECTION_FIELDS.get("milestone", {}).get("required", []):
                    if field not in milestone or not milestone[field]:
                        messages.append(("error", f"里程碑 #{i+1} 缺少必填字段: {field}"))
                        if field == "title":
                            milestone["title"] = f"里程碑 {i+1}"
                            need_fix = True

                # 确保有ID
                if "id" not in milestone:
                    if "title" in milestone:
                        milestone_id = f"milestone-{milestone['title'].lower().replace(' ', '-')}"
                    else:
                        milestone_id = f"milestone-{i+1}"
                    milestone["id"] = milestone_id
                    messages.append(("info", f"为里程碑生成ID: {milestone_id}"))
                    need_fix = True

                # 检查状态值
                if "status" in milestone and isinstance(milestone["status"], str):
                    status = milestone["status"].lower()
                    if status not in [s.lower() for s in VALID_STATUS]:
                        messages.append(("warning", f"里程碑 #{i+1} 状态值 '{status}' 不是标准状态"))
                        milestone["status"] = "planned"
                        need_fix = True

        # 验证任务
        if "tasks" in data and isinstance(data["tasks"], list):
            tasks = fixed_data["tasks"]
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    messages.append(("error", f"任务 #{i+1} 不是有效的对象"))
                    continue

                # 检查必填字段
                for field in SECTION_FIELDS.get("task", {}).get("required", []):
                    if field not in task or not task[field]:
                        messages.append(("error", f"任务 #{i+1} 缺少必填字段: {field}"))
                        if field == "title":
                            task["title"] = f"任务 {i+1}"
                            need_fix = True

                # 确保有ID
                if "id" not in task:
                    if "title" in task:
                        task_id = f"task-{task['title'].lower().replace(' ', '-')}"
                    else:
                        task_id = f"task-{i+1}"
                    task["id"] = task_id
                    messages.append(("info", f"为任务生成ID: {task_id}"))
                    need_fix = True

                # 检查状态值
                if "status" in task and isinstance(task["status"], str):
                    status = task["status"].lower()
                    if status not in [s.lower() for s in VALID_STATUS]:
                        messages.append(("warning", f"任务 #{i+1} 状态值 '{status}' 不是标准状态"))
                        task["status"] = "todo"
                        need_fix = True

                # 检查优先级
                if "priority" in task and isinstance(task["priority"], str):
                    priority = task["priority"].lower()
                    if priority not in [p.lower() for p in VALID_PRIORITY]:
                        messages.append(("warning", f"任务 #{i+1} 优先级 '{priority}' 不是标准优先级"))
                        task["priority"] = "medium"
                        need_fix = True

                # 处理引用转换（milestone/story/epic -> *_id）
                for ref_field, id_field, section_type in [
                    ("milestone", "milestone_id", "milestone"),
                    ("epic", "epic_id", "epic"),
                    ("story", "story_id", "story"),
                ]:
                    if ref_field in task and id_field not in task:
                        ref_value = task.pop(ref_field)
                        if isinstance(ref_value, str):
                            id_value = f"{section_type}-{ref_value.lower().replace(' ', '-')}"
                            task[id_field] = id_value
                            messages.append(("info", f"将 {ref_field} 引用转换为 {id_field}: {id_value}"))
                            need_fix = True

        # 验证史诗
        if "epics" in data and isinstance(data["epics"], list):
            epics = fixed_data["epics"]
            for i, epic in enumerate(epics):
                if not isinstance(epic, dict):
                    messages.append(("error", f"史诗 #{i+1} 不是有效的对象"))
                    continue

                # 检查必填字段
                for field in SECTION_FIELDS.get("epic", {}).get("required", []):
                    if field not in epic or not epic[field]:
                        messages.append(("error", f"史诗 #{i+1} 缺少必填字段: {field}"))
                        if field == "title":
                            epic["title"] = f"史诗 {i+1}"
                            need_fix = True

                # 确保有ID
                if "id" not in epic:
                    if "title" in epic:
                        epic_id = f"epic-{epic['title'].lower().replace(' ', '-')}"
                    else:
                        epic_id = f"epic-{i+1}"
                    epic["id"] = epic_id
                    messages.append(("info", f"为史诗生成ID: {epic_id}"))
                    need_fix = True

        # 验证故事
        if "stories" in data and isinstance(data["stories"], list):
            stories = fixed_data["stories"]
            for i, story in enumerate(stories):
                if not isinstance(story, dict):
                    messages.append(("error", f"故事 #{i+1} 不是有效的对象"))
                    continue

                # 检查必填字段
                for field in SECTION_FIELDS.get("story", {}).get("required", []):
                    if field not in story or not story[field]:
                        messages.append(("error", f"故事 #{i+1} 缺少必填字段: {field}"))
                        if field == "title":
                            story["title"] = f"故事 {i+1}"
                            need_fix = True

                # 确保有ID
                if "id" not in story:
                    if "title" in story:
                        story_id = f"story-{story['title'].lower().replace(' ', '-')}"
                    else:
                        story_id = f"story-{i+1}"
                    story["id"] = story_id
                    messages.append(("info", f"为故事生成ID: {story_id}"))
                    need_fix = True

                # 处理引用转换（milestone/epic -> *_id）
                for ref_field, id_field, section_type in [("milestone", "milestone_id", "milestone"), ("epic", "epic_id", "epic")]:
                    if ref_field in story and id_field not in story:
                        ref_value = story.pop(ref_field)
                        if isinstance(ref_value, str):
                            id_value = f"{section_type}-{ref_value.lower().replace(' ', '-')}"
                            story[id_field] = id_value
                            messages.append(("info", f"将 {ref_field} 引用转换为 {id_field}: {id_value}"))
                            need_fix = True

        return True if not need_fix else (len([m for m in messages if m[0] == "error"]) == 0), messages, fixed_data if need_fix else None

    def check_and_suggest(self, yaml_file: str, fix: bool = False) -> Tuple[bool, str]:
        """
        检查YAML文件并提供建议

        Args:
            yaml_file: YAML文件路径
            fix: 是否自动修复

        Returns:
            Tuple[bool, str]:
                - 是否有效
                - 消息字符串
        """
        is_valid, messages, fixed_data = self.validate(yaml_file)

        output_lines = []
        if is_valid and not messages:
            output_lines.append(f"✅ 文件格式正确: {yaml_file}")
            return True, "\n".join(output_lines)

        # 处理错误和警告
        for msg_type, msg in messages:
            if msg_type == "error":
                prefix = "❌ 错误"
            elif msg_type == "warning":
                prefix = "⚠️ 警告"
            else:
                prefix = "ℹ️ 信息"
            output_lines.append(f"{prefix}: {msg}")

        if not is_valid:
            if fix and fixed_data:
                # 生成修复后的文件
                fixed_file = f"{os.path.splitext(yaml_file)[0]}_fixed.yaml"
                self.generate_fixed_yaml(fixed_data, fixed_file)
                output_lines.append(f"\n✅ 已自动修复并保存到: {fixed_file}")
            else:
                output_lines.append("\n💡 提示: 使用 --fix 参数可以自动修复这些问题")

        return is_valid, "\n".join(output_lines)

    def generate_fixed_yaml(self, data: Dict[str, Any], output_path: str) -> None:
        """
        生成修复后的YAML文件

        Args:
            data: 修复后的数据
            output_path: 输出文件路径
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            logger.info(f"生成修复后的YAML文件: {output_path}")
        except Exception as e:
            logger.error(f"生成修复后的YAML文件失败: {str(e)}")

    def show_template(self) -> str:
        """
        获取标准模板

        Returns:
            str: 模板内容
        """
        # 使用自定义模板或默认模板
        if self.template_path and os.path.exists(self.template_path):
            with open(self.template_path, "r", encoding="utf-8") as f:
                return f.read()

        # 默认模板
        template = {
            "metadata": {
                "title": "Roadmap Title",
                "description": "Roadmap Description",
                "version": "1.0",
                "created_at": "2023-01-01",
                "updated_at": "2023-01-01",
                "author": "Author Name",
            },
            "milestones": [
                {
                    "id": "M1",
                    "title": "Milestone 1",
                    "description": "First milestone description",
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-31",
                    "status": "in_progress",
                }
            ],
            "tasks": [
                {
                    "id": "T1",
                    "title": "Task 1",
                    "description": "Task description",
                    "milestone_id": "M1",
                    "status": "in_progress",
                    "priority": "medium",
                    "assignee": "Assignee Name",
                    "tags": ["tag1", "tag2"],
                }
            ],
        }

        return yaml.dump(template, default_flow_style=False, allow_unicode=True, sort_keys=False)
