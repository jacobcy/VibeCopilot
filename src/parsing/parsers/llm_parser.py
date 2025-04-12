"""
LLM解析器

使用LLM服务进行内容解析的统一实现。
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from src.llm.service_factory import create_llm_service
from src.parsing.base_parser import BaseParser
from src.parsing.prompt_templates import get_prompt_template

logger = logging.getLogger(__name__)

# 定义项目根目录和临时目录常量
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEMP_ROOT = os.path.join(PROJECT_ROOT, "temp")


class LLMParser(BaseParser):
    """
    LLM解析器

    使用不同的LLM服务解析内容的统一实现。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化LLM解析器

        Args:
            config: 配置参数，包含provider信息
        """
        super().__init__(config)

        self.config = config or {}
        self.provider = self.config.get("provider", "openai")

        try:
            # 创建LLM服务实例
            self.llm_service = create_llm_service(self.provider, self.config)
        except Exception as e:
            raise

        # 初始化缓存
        self._cache = {}

        # 系统提示
        self.system_prompts = {
            "workflow": """你是一个专业的工作流分析专家。你的任务是：
1. 仔细分析规则文档中定义的流程
2. 根据提供的模板结构，识别流程中的各个阶段、检查项和交付物
3. 理解阶段之间的转换关系和条件
4. 将分析结果转换为结构化的JSON格式
5. 确保输出的JSON格式完全符合模板要求的结构""",
            "roadmap": """你是一个专业的路线图结构化专家。你的任务是：
1. 仔细分析提供的路线图YAML内容
2. 将内容转换为标准的epic-story-task结构
3. 确保所有字段名和值符合标准格式
4. 特别注意将milestone结构转换为epic-story结构
5. 确保priority字段使用标准值(low, medium, high, critical)
6. 将结果以JSON格式返回，不要包含任何解释性文本
7. 确保输出的JSON格式完全符合要求的结构""",
            "generic": "You are a helpful assistant that parses content accurately.",
        }

    def get_temp_dir(self, sub_dir=None, use_timestamp=True):
        """获取项目临时目录路径

        Args:
            sub_dir: 可选的子目录名
            use_timestamp: 是否使用时间戳创建子目录，默认为True

        Returns:
            str: 临时目录的绝对路径
        """
        # 获取当前时间戳作为目录名
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # 如果提供了子目录名，则在temp下创建特定类型的子目录
        if sub_dir:
            # 首先创建类型子目录
            type_dir = os.path.join(TEMP_ROOT, sub_dir)
            os.makedirs(type_dir, exist_ok=True)

            # 如果需要时间戳子目录
            if use_timestamp:
                # 在类型子目录下创建时间戳子目录
                timestamped_dir = os.path.join(type_dir, timestamp)
                os.makedirs(timestamped_dir, exist_ok=True)
                return timestamped_dir

            return type_dir

        # 如果没有提供子目录名，则直接返回基础temp目录
        os.makedirs(TEMP_ROOT, exist_ok=True)
        return TEMP_ROOT

    async def parse_text(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        使用LLM服务解析文本内容

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如'rule'、'document'等

        Returns:
            解析结果
        """
        # 如果未指定内容类型，默认为通用类型
        content_type = content_type or "generic"

        # 获取对应的提示模板
        prompt_template = get_prompt_template(content_type)

        # 获取系统提示
        system_prompt = self.system_prompts.get(content_type, "You are a helpful assistant that parses content accurately.")

        # 格式化提示
        prompt = prompt_template.format(content=content)

        # 准备消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        logger.info(f"使用 {content_type} 提示模板进行解析")

        # 创建临时文件来保存请求内容
        # 获取当前时间戳
        timestamp = int(time.time())

        # 创建时间戳子目录
        timestamp_dir = self.get_temp_dir("llm_logs")

        # 保存请求内容
        request_file = os.path.join(timestamp_dir, f"request_{timestamp}.txt")
        with open(request_file, "w", encoding="utf-8") as f:
            # 保存详细请求内容，包括系统提示和用户提示
            f.write(f"内容类型: {content_type}\n\n")
            f.write(f"系统提示:\n{system_prompt}\n\n")
            f.write(f"用户提示:\n{prompt}\n\n")
            f.write(f"原始内容:\n{content}")
        logger.info(f"📝 已保存LLM请求内容到: {request_file}")

        # 用于存储原始响应文本，即使发生异常也能保存
        result_text = ""

        # 调用LLM服务
        try:
            logger.info("🚀 开始调用LLM服务...")
            response = await self.llm_service.chat_completion(messages)
            logger.info("✅ LLM服务调用成功")

            # 根据不同的LLM服务提供者处理响应
            if hasattr(response, "choices") and hasattr(response.choices[0], "message"):
                # OpenAI API的原生对象格式
                result_text = response.choices[0].message.content
            else:
                # 字典格式的响应
                result_text = response["choices"][0]["message"]["content"]

            logger.info("📥 获取到LLM响应，开始处理")

            # 保存原始LLM响应 - 对所有内容类型都记录
            try:
                # 使用与请求相同的时间戳目录
                response_file = os.path.join(timestamp_dir, f"response_{timestamp}.txt")
                with open(response_file, "w", encoding="utf-8") as f:
                    f.write(result_text)
                logger.info(f"📝 已保存LLM原始响应到: {response_file}")
            except Exception as e:
                logger.warning(f"⚠️ 无法保存LLM原始响应: {str(e)}")

            logger.debug(f"LLM原始响应内容: {result_text[:200]}...")

            # 尝试解析JSON响应
            if content_type == "roadmap" or content_type == "workflow":
                try:
                    import json

                    # 尝试直接解析为JSON
                    try:
                        json_result = json.loads(result_text)
                        logger.info("成功解析为JSON对象")
                        # 对于路线图专门处理
                        if content_type == "roadmap":
                            return {"success": True, "content_type": "roadmap", "content": json_result, "raw_response": result_text}  # 添加原始响应
                    except json.JSONDecodeError as je:
                        # 尝试从非标准格式中提取JSON
                        logger.warning(f"直接JSON解析失败: {str(je)}，尝试从文本提取JSON部分")
                        # 查找可能的JSON部分标记
                        json_start_markers = ["{", "{\n", "```json\n{", "```\n{", "```json\n"]
                        json_end_markers = ["}", "\n}", "}\n```", "}\n", "\n}\n```"]

                        json_extracted = False
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
                                        json_result = json.loads(json_text)
                                        logger.info(f"成功从部分文本中提取JSON对象: 从{start_index}到{end_index}")
                                        # 对于路线图专门处理
                                        if content_type == "roadmap":
                                            return {
                                                "success": True,
                                                "content_type": "roadmap",
                                                "content": json_result,
                                                "raw_response": result_text,  # 添加原始响应
                                            }
                                        json_extracted = True
                                        break
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"提取的JSON部分解析失败: {str(e)}, 文本: {json_text[:50]}...")

                        # 如果未能提取JSON，把原始响应作为YAML处理
                        if not json_extracted:
                            logger.warning("无法从响应中提取JSON，尝试作为YAML处理")
                            try:
                                import yaml

                                yaml_data = yaml.safe_load(result_text)
                                if isinstance(yaml_data, dict):
                                    logger.info("成功将响应解析为YAML")
                                    return {"success": True, "content_type": "roadmap", "content": yaml_data, "raw_response": result_text}  # 添加原始响应
                            except yaml.YAMLError as ye:
                                logger.warning(f"YAML解析也失败: {str(ye)}")

                            # 返回原始文本，作为内容预览
                            return {
                                "success": False,
                                "error": f"无法解析LLM响应为JSON或YAML",
                                "content_type": content_type,
                                "content_preview": result_text[:300] + "..." if len(result_text) > 300 else result_text,
                                "raw_response": result_text,
                            }

                except Exception as e:
                    logger.error(f"处理JSON响应时出错: {str(e)}")
                    return {
                        "success": False,
                        "error": f"处理JSON响应出错: {str(e)}",
                        "content_type": content_type,
                        "content_preview": result_text[:300] + "..." if len(result_text) > 300 else result_text,
                        "raw_response": result_text,
                    }

            # 根据内容类型处理结果
            content_processors = {
                "workflow": self._process_workflow_response,
                "rule": self._process_rule_response,
                "document": self._process_document_response,
                "generic": self._process_generic_response,
            }

            processor = content_processors.get(content_type, self._process_generic_response)
            return processor(content, result_text)

        except Exception as e:
            logger.error(f"LLM服务调用或响应处理失败: {str(e)}")

            # 即使发生异常，也创建一个调试文件，标明解析出错
            if content_type == "roadmap":
                try:
                    # 使用项目目录下的临时目录
                    llm_log_dir = self.get_temp_dir("llm_logs")

                    error_response_file = os.path.join(llm_log_dir, f"llm_error_response_{int(time.time())}.txt")
                    with open(error_response_file, "w", encoding="utf-8") as f:
                        error_msg = f"LLM解析过程中出现异常: {str(e)}\n\n"
                        if result_text:
                            error_msg += f"获取到的部分响应:\n{result_text}"
                        else:
                            error_msg += "未能获取任何响应。"
                        f.write(error_msg)
                    logger.info(f"📝 已保存LLM错误信息到: {error_response_file}")
                except Exception as write_err:
                    logger.warning(f"⚠️ 无法保存错误信息: {str(write_err)}")

            return {
                "success": False,
                "error": str(e),
                "content_type": content_type,
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "raw_response": result_text if result_text else "解析过程中发生异常，未能获取响应",
            }

    def _process_workflow_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理工作流响应"""
        try:
            # 尝试解析JSON响应
            workflow_data = json.loads(result_text)

            return {"success": True, "content_type": "workflow", "content": workflow_data}
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON response: {str(e)}",
                "content_type": "workflow",
                "content_preview": result_text[:100] + "...",
            }

    def _process_rule_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理规则响应"""
        # 直接通过基本的方法提取Front Matter和标题
        front_matter = {}
        markdown_content = content

        # 简单解析Front Matter
        if content.startswith("---"):
            try:
                end_index = content.find("---", 3)
                if end_index != -1:
                    front_matter_text = content[3:end_index].strip()
                    for line in front_matter_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            front_matter[key.strip()] = value.strip()

                    markdown_content = content[end_index + 3 :].strip()
            except Exception:
                pass

        # 提取标题
        title = ""
        lines = markdown_content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        return {
            "success": True,
            "content_type": "rule",
            "front_matter": front_matter,
            "title": title,
            "content": markdown_content,
            "metadata": {
                "title": title,
                "type": front_matter.get("type", "unknown"),
                "description": front_matter.get("description", ""),
                "tags": front_matter.get("tags", "").split(",") if front_matter.get("tags") else [],
            },
        }

    def _process_document_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理文档响应"""
        # 提取标题和目录结构
        title = ""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # 简单解析目录结构
        headings = []
        for line in lines:
            if line.startswith("#"):
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                heading_text = line[level:].strip()
                headings.append({"level": level, "text": heading_text})

        return {
            "success": True,
            "content_type": "document",
            "title": title,
            "content": content,
            "structure": {"headings": headings},
            "metadata": {
                "title": title,
                "word_count": len(content.split()),
                "line_count": len(lines),
            },
        }

    def _process_generic_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理通用响应"""
        lines = content.split("\n")

        return {
            "success": True,
            "content_type": "generic",
            "content": content,
            "result": result_text,
            "metadata": {
                "line_count": len(lines),
                "word_count": len(content.split()),
                "char_count": len(content),
            },
        }

    def parse(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        同步方法，解析文本内容

        这是一个适配方法，允许在同步上下文中使用LLM解析器。
        LLMParser总是使用LLM服务进行解析，保持职责单一。

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如'rule'、'document'等

        Returns:
            解析结果
        """
        import asyncio

        import nest_asyncio

        # 尝试安装和启用nest_asyncio，允许在同步上下文中运行异步代码
        try:
            nest_asyncio.apply()
        except Exception as e:
            logger.error(f"无法启用nest_asyncio: {str(e)}，LLM解析可能无法在同步上下文中工作")
            return {
                "success": False,
                "error": f"环境配置错误，无法启用nest_asyncio: {str(e)}",
                "content_type": content_type or "generic",
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }

        try:
            logger.info("使用LLM服务进行解析")

            # 生成时间戳
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            timestamp_unix = int(time.time())

            # 使用项目目录下的临时目录
            timestamp_dir = self.get_temp_dir("llm_logs")

            # 保存请求内容
            request_file = os.path.join(timestamp_dir, f"request_{timestamp_unix}.txt")
            try:
                with open(request_file, "w", encoding="utf-8") as f:
                    # 保存详细请求内容，包括内容类型和原始内容
                    f.write(f"内容类型: {content_type}\n\n")
                    f.write(f"原始内容:\n{content}")
                logger.info(f"📝 已保存LLM请求内容到: {request_file}")
            except Exception as e:
                logger.warning(f"⚠️ 无法保存LLM请求内容: {str(e)}")

            # 使用asyncio运行异步函数
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self.parse_text(content, content_type))

            # 保存响应内容
            response_file = os.path.join(timestamp_dir, f"response_{timestamp_unix}.txt")
            try:
                with open(response_file, "w", encoding="utf-8") as f:
                    if "raw_response" in result:
                        f.write(result["raw_response"])
                    else:
                        import json

                        f.write(json.dumps(result, indent=2, ensure_ascii=False))
                logger.info(f"📝 已保存LLM响应内容到: {response_file}")
            except Exception as e:
                logger.warning(f"⚠️ 无法保存LLM响应内容: {str(e)}")

            return result
        except Exception as e:
            logger.error(f"❌ LLM解析失败: {str(e)}")

            error_result = {
                "success": False,
                "error": f"LLM解析失败: {str(e)}",
                "content_type": content_type or "generic",
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "original_error": str(e),
            }

            # 保存错误信息
            try:
                # 使用项目目录下的临时目录
                timestamp_dir = self.get_temp_dir("llm_logs")
                error_file = os.path.join(timestamp_dir, f"llm_parser_error_{timestamp_unix}.json")
                with open(error_file, "w", encoding="utf-8") as f:
                    json.dump(error_result, f, indent=2, ensure_ascii=False)
                logger.info(f"📝 已保存解析错误信息到: {error_file}")
            except Exception as write_err:
                logger.warning(f"⚠️ 无法保存解析错误文件: {str(write_err)}")

            return error_result
