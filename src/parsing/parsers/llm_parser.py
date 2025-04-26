"""
LLM解析器

使用LLM服务进行内容解析的统一实现。
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Get the logger instance at the module level
logger = logging.getLogger(__name__)

# Import json_repair
try:
    import json_repair

    # Test if it has the loads method
    if not hasattr(json_repair, "loads"):
        raise ImportError("json_repair found but 'loads' function is missing.")
    logger.info("json-repair library loaded successfully.")
except ImportError:
    json_repair = None
    logger.warning("json-repair library not found or invalid. Falling back to standard json parsing for structured data.")


from src.llm.service_factory import create_llm_service
from src.parsing.base_parser import BaseParser
from src.parsing.prompt_templates import get_prompt_template, get_system_prompt

# Import the new utility function
from src.utils.file_utils import ConfigError, get_data_path


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
            logger.error(f"Failed to create LLM service for provider '{self.provider}': {e}", exc_info=True)
            raise  # Re-raise the exception

        # 初始化缓存 (You might want to implement actual caching later)
        self._cache = {}

    def _get_temp_dir(self, sub_dir: Optional[str] = None) -> str:
        """获取用于LLM日志的临时目录，确保其唯一性。

        Args:
            sub_dir: 可选的子目录名称。

        Returns:
            临时目录的绝对路径。

        Raises:
            ValueError: 如果无法通过 get_data_path 确定数据目录。
        """
        try:
            # Generate a unique directory path using timestamp/UUID
            timestamp_dir = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
            final_sub_dir = os.path.join(sub_dir or "llm_logs", timestamp_dir)

            # Use get_data_path to construct the full path within the configured data/temp area
            base_temp_path = get_data_path("temp", final_sub_dir)

            if not base_temp_path:
                raise ValueError("`get_data_path` failed to return a valid path for the temporary directory.")

            # Ensure the directory exists
            os.makedirs(base_temp_path, exist_ok=True)
            logger.debug(f"Ensured temporary directory exists: {base_temp_path}")
            return base_temp_path

        except Exception as e:
            logger.error(f"创建或获取LLM临时日志目录失败: {e}", exc_info=True)
            # Re-raise the exception to make the error visible
            raise ValueError(f"Failed to create or access temporary LLM log directory: {e}") from e

    def _save_log_file(self, directory: str, prefix: str, timestamp: int, content: str) -> None:
        """安全地保存日志文件 (directory is now absolute path from _get_temp_dir)"""
        try:
            # directory is already the absolute path including timestamp
            # Ensure it exists one last time before writing (in case fallback was used)
            # Although _get_temp_dir tries to create it, double-check
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, f"{prefix}_{timestamp}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"📝 已保存日志文件到: {filepath}")
        except OSError as e:
            # Log which specific directory failed if possible
            logger.warning(f"⚠️ 无法写入日志文件 {prefix} 到 {directory}: {e}")
        except Exception as e:
            logger.warning(f"⚠️ 无法保存日志文件 {prefix}: {e}")

    def _prepare_request(self, content: str, content_type: str) -> Tuple[List[Dict[str, str]], str]:
        """准备LLM请求所需的消息和日志内容"""
        logger.debug(f"Preparing request for content_type: {content_type}")
        prompt_template = get_prompt_template(content_type)
        system_prompt = get_system_prompt(content_type)
        try:
            prompt = prompt_template.format(content=content)
        except KeyError as e:
            logger.error(f"提示模板 '{content_type}' 格式化错误，缺少键: {e}. Content: {content[:100]}...")
            raise ValueError(f"Prompt template formatting error for type '{content_type}': Missing key {e}") from e

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        request_log_content = (
            f"Content Type: {content_type}\n\n"
            f"System Prompt:\n{system_prompt}\n\n"
            f"User Prompt:\n{prompt}\n\n"
            f"Original Content Snippet:\n{content[:500]}...\n"  # Log only a snippet
        )

        return messages, request_log_content

    async def _execute_llm_call(self, messages: List[Dict[str, str]]) -> str:
        """执行LLM调用并提取原始响应文本"""
        logger.info("🚀 开始调用LLM服务...")
        try:
            response = await self.llm_service.chat_completion(messages)
            logger.info("✅ LLM服务调用成功")
        except Exception as e:
            logger.error(f"LLM服务调用失败: {e}", exc_info=True)
            raise  # Re-raise to be caught by the main parse_text method

        # Extract raw text based on provider response structure
        result_text = ""
        try:
            if hasattr(response, "choices") and response.choices and hasattr(response.choices[0], "message"):
                result_text = response.choices[0].message.content or ""  # Handle potential None
            elif isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
                message_content = response["choices"][0].get("message", {}).get("content", "")
                result_text = message_content if isinstance(message_content, str) else ""
            else:
                logger.warning(f"无法识别的LLM响应格式: {type(response)}。尝试将其转换为字符串。")
                result_text = str(response)
        except (IndexError, KeyError, AttributeError, TypeError) as e:
            logger.warning(f"从LLM响应中提取文本时出错: {e}. Response: {str(response)[:200]}...")
            result_text = str(response)  # Fallback to string representation

        logger.info(f"📥 获取到LLM响应，原始文本长度: {len(result_text)}")
        logger.debug(f"Raw LLM Response Snippet: {result_text[:200]}...")
        return result_text

    def _parse_structured_response(self, result_text: str, content_type: str) -> Dict[str, Any]:
        """使用json-repair (优先) 或标准库解析结构化响应 (workflow/roadmap)"""

        # 1. 尝试使用 json-repair (如果可用)
        if json_repair:
            logger.debug(f"Attempting to parse with json_repair for {content_type}...")
            try:
                # Use json_repair.loads which attempts to fix and parse
                parsed_data = json_repair.loads(result_text)

                if isinstance(parsed_data, dict):
                    logger.info(f"✅ 成功使用 json_repair 解析响应为字典对象 ({content_type})")
                    return {
                        "success": True,
                        "content_type": content_type,
                        "content": parsed_data,
                        "raw_response": result_text,
                    }
                else:
                    # Handle case where repair succeeds but result isn't a dict
                    logger.warning(f"json_repair 解析成功，但结果不是字典类型: {type(parsed_data)}. Snippet: {str(parsed_data)[:100]}...")
                    # Fall through to standard JSON parsing or failure

            except ValueError as e:  # json_repair raises ValueError on failure
                logger.warning(f"⚠️ json_repair 无法修复或解析响应 ({content_type}). Error: {e}. 将尝试标准 JSON 解析。")
            except Exception as e:  # Catch any other unexpected errors from json_repair
                logger.warning(f"⚠️ 使用 json_repair 解析时发生意外错误 ({content_type}): {e}. 将尝试标准 JSON 解析。", exc_info=True)

        # 2. 如果 json-repair 不可用或失败，尝试标准 json.loads
        logger.debug(f"Attempting standard JSON parse for {content_type}...")
        try:
            parsed_data = json.loads(result_text)
            logger.info("✅ 成功使用标准 json.loads 解析响应为JSON对象")
            return {
                "success": True,
                "content_type": content_type,
                "content": parsed_data,
                "raw_response": result_text,
            }
        except json.JSONDecodeError as e:
            error_msg = f"无法将LLM响应解析为JSON ({content_type}). 标准库错误: {e}"
            logger.error(error_msg)
            # Fall through to return failure

        # 3. 如果所有方法都失败
        final_error_message = f"无法将LLM响应解析为JSON ({content_type})，已尝试 json_repair (如果可用) 和标准库。"
        logger.error(final_error_message)
        return {
            "success": False,
            "error": final_error_message,
            "content_type": content_type,
            "content_preview": result_text[:300] + "...",
            "raw_response": result_text,
        }

    # --- Specific Processors (Kept for simple non-JSON types, could be refactored further) ---
    # These typically operate on the *original* content, not the LLM response usually.
    # Pass result_text if they need to analyze the LLM output instead/as well.

    def _process_rule_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理规则响应 (Simple extraction from original content)"""
        logger.debug("Processing rule response (simple extraction)...")
        front_matter = {}
        markdown_content = content
        title = ""
        try:
            if content.startswith("---"):
                end_index = content.find("---", 3)
                if end_index != -1:
                    front_matter_text = content[3:end_index].strip()
                    for line in front_matter_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            front_matter[key.strip()] = value.strip()
                    markdown_content = content[end_index + 3 :].strip()

            lines = markdown_content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        except Exception as e:
            logger.warning(f"Simple rule processing failed: {e}")
            # Return basic structure even if parsing fails
            markdown_content = content  # Reset to original if parsing failed
            title = "Unknown Title"
            front_matter = {}

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
            "raw_response": result_text,  # Include raw LLM response
        }

    def _process_document_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理文档响应 (Simple extraction from original content)"""
        logger.debug("Processing document response (simple extraction)...")
        title = ""
        headings = []
        lines = content.split("\n")
        try:
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            for line in lines:
                if line.startswith("#"):
                    level = 0
                    for char in line:  # Safer way to count leading '#'
                        if char == "#":
                            level += 1
                    else:
                        break
            if line[level:].startswith(" "):  # Ensure space after #
                heading_text = line[level:].strip()
                headings.append({"level": level, "text": heading_text})
        except Exception as e:
            logger.warning(f"Simple document processing failed: {e}")
            title = "Unknown Title"
            headings = []

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
            "raw_response": result_text,
        }

    def _process_generic_response(self, content: str, result_text: str) -> Dict[str, Any]:
        """处理通用响应 (Returns raw LLM result)"""
        logger.debug("Processing generic response...")
        return {
            "success": True,
            "content_type": "generic",
            "content": content,  # Original input content
            "result": result_text,  # Raw LLM output
            "metadata": {
                "line_count": len(content.split("\n")),
                "word_count": len(content.split()),
                "char_count": len(content),
            },
            "raw_response": result_text,
        }

    # --- Main Orchestration Method ---
    async def parse_text(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        使用LLM服务解析文本内容 (Orchestration Method)

        Args:
            content: 待解析的文本内容
            content_type: 内容类型，如\'rule\'、\'document\'等

        Returns:
            解析结果
        """
        content_type = content_type or "generic"
        timestamp = int(time.time())
        # Use microseconds for log dir uniqueness if many requests happen in one second
        timestamp_dir = self._get_temp_dir(f"llm_logs/{content_type}")
        result_text = ""  # Initialize for potential use in exception handlers

        try:
            # 1. Prepare Request
            messages, request_log_content = self._prepare_request(content, content_type)
            self._save_log_file(timestamp_dir, "request", timestamp, request_log_content)

            # 2. Execute LLM Call
            result_text = await self._execute_llm_call(messages)
            self._save_log_file(timestamp_dir, "response", timestamp, result_text)

            # 3. Parse/Process Response based on type
            if content_type in ["workflow", "roadmap"]:
                # Use the dedicated parsing method with json-repair
                return self._parse_structured_response(result_text, content_type)
            else:
                # Fallback to specific simple processors or generic one
                logger.debug(f"Using simple/generic processor for content type: {content_type}")
                content_processors = {
                    "rule": self._process_rule_response,
                    "document": self._process_document_response,
                    # Add other specific processors if they exist
                }
                # Use generic processor if no specific one is found
                processor = content_processors.get(content_type, self._process_generic_response)
                return processor(content, result_text)

        except Exception as e:
            # General exception handling for call or parsing logic errors
            error_msg = f"LLM解析流程失败 ({content_type}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Save error log
            error_log_content = f"LLM解析过程中出现异常: {e}\n\n"
            error_log_content += f"Content Type: {content_type}\n\n"
            if result_text:
                error_log_content += f"获取到的响应 (可能不完整):\n{result_text}"
            else:
                error_log_content += "未能获取任何响应或在获取响应前发生错误。"
            self._save_log_file(timestamp_dir, f"llm_error", timestamp, error_log_content)

            return {
                "success": False,
                "error": error_msg,
                "content_type": content_type,
                "content_preview": content[:100] + "...",
                "raw_response": result_text if result_text else "解析过程中发生异常，未能获取响应",
            }

    # --- Sync Wrapper (Kept for compatibility) ---
    def parse(self, content: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        同步方法，解析文本内容

        这是一个适配方法，允许在同步上下文中使用LLM解析器。
        """
        import asyncio

        # Correct way to run async from sync: use asyncio.run() if possible,
        # or manage event loop if running inside another loop.
        # Assuming this parse() is called from a top-level sync context.
        try:
            # Use asyncio.run() for simplicity if possible.
            # If this needs to integrate with an existing loop (e.g., FastAPI),
            # the calling code needs to handle the await differently.
            logger.info("运行异步 LLM 解析 (Sync Wrapper)...")
            result = asyncio.run(self.parse_text(content, content_type))
            return result
        except RuntimeError as e:
            # Handle cases where asyncio.run() can't be used (e.g., nested loops)
            if "cannot be called from a running event loop" in str(e):
                logger.error("同步 `parse` 方法不能从正在运行的事件循环中调用。请直接 `await parse_text`。")
                return {"success": False, "error": "Async context error: Cannot run nested event loops."}
            else:
                logger.error(f"❌ LLM解析失败 (Sync Wrapper - Runtime Error): {str(e)}", exc_info=True)
                # ... (log error to file?) ...
                return {
                    "success": False,
                    "error": f"LLM解析失败 (Runtime Error): {str(e)}",
                    "content_type": content_type or "generic",
                    "content_preview": content[:100] + "...",
                }
        except Exception as e:
            logger.error(f"❌ LLM解析失败 (Sync Wrapper - General Error): {str(e)}", exc_info=True)
            # ... (log error to file?) ...
            # ... (error return structure) ...
            return {
                "success": False,
                "error": f"LLM解析失败: {str(e)}",
                "content_type": content_type or "generic",
                "content_preview": content[:100] + "...",
                "original_error": str(e),
            }
