"""
路线图处理器

用于路线图数据的智能解析和结构转换，主要功能包括：
1. 将不规范的YAML转换为正确的路线图结构
2. 将milestone格式转换为epic-story-task结构
3. 修复常见的结构问题
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import yaml

from src.llm.service_factory import create_llm_service
from src.validation.roadmap_validation import RoadmapValidator

logger = logging.getLogger(__name__)

# 定义项目根目录和临时目录常量
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMP_ROOT = os.path.join(PROJECT_ROOT, "temp")


class RoadmapProcessor:
    """路线图数据处理器 - 仅使用LLM解析"""

    def __init__(self):
        """初始化路线图处理器"""
        # 创建LLM服务实例
        config = {"provider": "openai", "format": "yaml", "content_type": "roadmap"}
        self.llm_service = create_llm_service("openai", config)

        # 初始化验证器
        try:
            self.validator = RoadmapValidator()
        except Exception as e:
            logger.warning(f"初始化验证器失败: {str(e)}，将使用None")
            self.validator = None

        # 添加字段映射和优先级转换的字典
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

        # 系统提示
        self.system_prompt = """你是一个专业的路线图结构化专家。你的任务是：
1. 仔细分析提供的路线图YAML内容
2. 将内容转换为标准的epic-story-task结构
3. 确保输出包含完整的metadata部分（必须包含），至少要有title和version字段
4. 确保所有字段名和值符合标准格式
5. 特别注意将milestone结构转换为epic-story结构
6. 确保priority字段使用标准值(low, medium, high, critical)
7. 输出的标准结构必须包含以下必要字段：
   - metadata部分：包含title和version字段
   - epics数组：包含title和stories字段
   - 每个epic下的stories数组：每个story至少包含title字段和一个tasks数组
   - 每个story的tasks数组：每个task至少包含title字段和status字段
8. 将结果以JSON格式返回，不要包含任何解释性文本
9. 确保输出的JSON格式完全符合要求的结构"""

    def get_temp_file(self, filename: str) -> str:
        """获取临时文件路径"""
        if not self._timestamp_dir:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            roadmap_dir = os.path.join(TEMP_ROOT, "roadmap")
            os.makedirs(roadmap_dir, exist_ok=True)
            self._timestamp_dir = os.path.join(roadmap_dir, timestamp)
            os.makedirs(self._timestamp_dir, exist_ok=True)

        return os.path.join(self._timestamp_dir, filename)

    async def parse_roadmap(self, content: str) -> Dict[str, Any]:
        """使用LLM解析路线图内容"""
        # 保存原始内容用于调试
        debug_file = self.get_temp_file("original_yaml_content.yaml")
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📝 已保存原始YAML内容到: {debug_file}")
        except Exception as e:
            logger.warning(f"⚠️ 无法保存原始内容调试文件: {str(e)}")

        logger.info("🚀 使用LLM解析roadmap")

        # 准备消息 - 使用非常简洁的方式
        user_message = "请将以下路线图内容解析为标准结构：\n\n" + content + "\n\n"

        # 添加要求返回JSON内容的信息
        user_message += "请将内容转换为标准的epic-story-task结构，并确保包含metadata部分。\n"
        user_message += "输出格式应为JSON，包含metadata（至少有title和version字段）和epics数组。\n"
        user_message += "每个epic应包含至少title和stories字段。\n"
        user_message += "每个story必须包含title字段和tasks数组，即使tasks为空也要提供该数组。\n"
        user_message += "每个task至少应包含title和status字段。\n"
        user_message += "不要包含任何解释性文本，只输出JSON内容。"

        # 引用简单示例
        user_message += '\n\n结构示例：{"metadata":{"title":"...","version":"..."},"epics":[{"title":"...","stories":[{"title":"...","tasks":[{"title":"...","status":"..."}]}]}]}'

        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_message}]

        # 保存请求内容
        request_file = self.get_temp_file("roadmap_llm_request.yaml")
        try:
            with open(request_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📝 已保存发送给LLM的原始请求内容到: {request_file}")
        except Exception as e:
            logger.warning(f"⚠️ 无法保存LLM请求内容: {str(e)}")

        # 调用LLM服务
        try:
            logger.info("🚀 开始调用LLM服务...")
            response = await self.llm_service.chat_completion(messages)
            logger.info("✅ LLM服务调用成功")

            # 处理响应
            if hasattr(response, "choices") and hasattr(response.choices[0], "message"):
                # OpenAI API的原生对象格式
                result_text = response.choices[0].message.content
            else:
                # 字典格式的响应
                result_text = response["choices"][0]["message"]["content"]

            # 保存LLM完整原始响应以便调试
            raw_response_file = self.get_temp_file("llm_response_result.json")
            try:
                with open(raw_response_file, "w", encoding="utf-8") as f:
                    f.write(result_text)
                logger.info(f"📝 已保存LLM完整原始响应到: {raw_response_file}")
            except Exception as e:
                logger.warning(f"⚠️ 无法保存LLM完整原始响应: {str(e)}")

            # 从LLM响应中提取JSON数据
            processed_data = self._extract_processed_data(result_text)

            if processed_data is None:
                return self._generate_error_result("无法从LLM响应中提取有效数据")

            # 确保有metadata部分
            if "metadata" not in processed_data:
                processed_data["metadata"] = {"title": "路线图", "version": "1.0", "description": "使用LLM解析生成"}
                logger.warning("⚠️ 添加缺失的metadata部分")

            # 修复字段映射、优先级格式和空状态值
            processed_data = self.fix_field_mapping(processed_data)
            processed_data = self.fix_priority_format(processed_data)
            processed_data = self.fix_empty_status(processed_data)

            # 保存处理后的数据
            processed_file = self.get_temp_file("roadmap_llm_processed_data.json")
            try:
                with open(processed_file, "w", encoding="utf-8") as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                logger.info(f"📝 已保存处理后的数据到: {processed_file}")
            except Exception as e:
                logger.warning(f"⚠️ 无法保存处理后的数据: {str(e)}")

            # 对LLM解析结果进行验证
            is_valid = self.validator and self.validator.validate(processed_data)

            if is_valid:
                logger.info("✅ LLM解析结果验证通过")
                return processed_data
            else:
                # 记录验证失败的详情但仍返回数据
                warnings = self.validator.get_warnings() if self.validator else []
                errors = self.validator.get_errors() if self.validator else ["没有验证器实例"]
                logger.warning(f"⚠️ LLM解析成功但验证失败: {len(errors)}个错误, {len(warnings)}个警告")
                return processed_data

        except Exception as e:
            return self._handle_exception(e)

    def _extract_processed_data(self, result_text: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取有效数据"""
        processed_data = None

        # 尝试直接解析为JSON
        try:
            processed_data = json.loads(result_text)
            if isinstance(processed_data, dict):
                logger.info("✅ 成功将LLM响应解析为JSON对象")
                return processed_data
        except json.JSONDecodeError:
            logger.warning("⚠️ 直接JSON解析失败，尝试提取JSON部分")

        # 尝试从响应中提取JSON部分
        json_start_markers = ["{", "{\n", "```json\n{", "```\n{", "```json\n"]
        json_end_markers = ["}", "\n}", "}\n```", "}\n", "\n}\n```"]

        for start_marker in json_start_markers:
            if start_marker in result_text:
                start_index = result_text.find(start_marker)
                if start_marker not in ["{", "{\n"]:
                    start_index += len(start_marker) - 1  # 减去1是为了保留{

                # 查找结束标记
                end_index = -1
                for end_marker in json_end_markers:
                    if end_marker in result_text[start_index:]:
                        # 这里+1是为了包含结束的}
                        end_index = result_text.find(end_marker, start_index) + 1
                        break

                if end_index > start_index:
                    json_text = result_text[start_index:end_index]
                    try:
                        processed_data = json.loads(json_text)
                        if isinstance(processed_data, dict):
                            logger.info(f"✅ 成功从部分文本中提取JSON对象")
                            return processed_data
                    except json.JSONDecodeError:
                        logger.warning("⚠️ 提取的JSON部分解析失败")

        # 尝试作为YAML解析
        try:
            yaml_data = yaml.safe_load(result_text)
            if isinstance(yaml_data, dict):
                logger.info("✅ 成功将响应解析为YAML")
                return yaml_data
        except Exception:
            logger.warning("⚠️ YAML解析也失败")

        return None

    def _generate_error_result(self, error_message: str) -> Dict[str, Any]:
        """生成错误结果"""
        logger.error(f"❌ {error_message}")

        # 生成错误结果
        error_result = {"metadata": {"title": "LLM解析失败", "description": error_message, "version": "0.1", "error": True}, "epics": []}

        return error_result

    def _handle_exception(self, e: Exception) -> Dict[str, Any]:
        """处理异常"""
        import traceback

        error_message = f"LLM解析过程出现异常: {str(e)}"
        logger.error(f"❌ {error_message}")

        # 获取异常堆栈
        error_traceback = traceback.format_exc()

        # 保存异常信息
        error_file = self.get_temp_file("roadmap_llm_exception.txt")
        try:
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(f"异常信息: {str(e)}\n\n详细堆栈:\n{error_traceback}")
            logger.info(f"📝 已保存异常详细信息到: {error_file}")
        except Exception as write_err:
            logger.warning(f"⚠️ 无法保存异常信息文件: {str(write_err)}")

        # 返回错误结果
        return {
            "metadata": {
                "title": "路线图解析异常",
                "description": error_message,
                "version": "0.1",
                "error": True,
                "error_details": error_traceback.split("\n")[:5],  # 包含前5行异常堆栈
            },
            "epics": [],
        }

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

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """处理路线图YAML文件"""
        logger.info(f"开始处理文件: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 使用事件循环运行异步函数
            if loop.is_running():
                result = loop.run_until_complete(self.parse_roadmap(content))
            else:
                result = asyncio.run(self.parse_roadmap(content))

            logger.info("文件处理成功")
            return result

        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            raise

    async def fix_file(self, file_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """修复路线图YAML文件"""
        logger.info(f"开始修复文件: {file_path}")

        if not output_path:
            basename = os.path.basename(file_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(os.path.dirname(file_path), f"{name}_fixed{ext}")

        try:
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 直接调用异步解析方法
            data = await self.parse_roadmap(content)

            # 验证处理后的数据
            is_valid = self.validator.validate(data) if self.validator else True

            if not is_valid and self.validator:
                warnings_str = "\n".join(self.validator.get_warnings())
                errors_str = "\n".join(self.validator.get_errors())
                logger.warning(f"修复后的数据仍有问题:\n警告:\n{warnings_str}\n错误:\n{errors_str}")

            # 写入输出文件
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logger.info(f"成功修复文件并保存到: {output_path}")
            return True, output_path

        except Exception as e:
            error_msg = f"修复文件失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# 导出类
__all__ = ["RoadmapProcessor"]
