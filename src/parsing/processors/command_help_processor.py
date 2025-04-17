"""
命令帮助信息与配置对比处理器

使用LLM将命令的 --help 输出与YAML配置进行对比，找出差异。
"""

import json
import logging
from typing import Any, Dict, Optional

from src.parsing.base_parser import BaseParser  # 可选，看是否需要继承
from src.parsing.parsers.llm_parser import LLMParser

logger = logging.getLogger(__name__)


class CommandHelpProcessor:
    """
    使用LLM对比命令帮助信息和预期配置。
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        初始化处理器。

        Args:
            llm_config: 传递给 LLMParser 的配置。
        """
        self.llm_config = llm_config or {}
        try:
            # 在需要时创建 LLMParser 实例
            self.llm_parser = LLMParser(self.llm_config)
            logger.info("CommandHelpProcessor initialized with LLMParser.")
        except Exception as e:
            logger.error(f"Failed to initialize LLMParser in CommandHelpProcessor: {e}", exc_info=True)
            # 可以选择抛出异常或设置一个错误状态
            raise RuntimeError(f"Failed to initialize LLMParser: {e}") from e

    def compare(self, help_text: str, cmd_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        对比帮助文本和命令配置。

        Args:
            help_text: 命令的 --help 输出。
            cmd_config: 命令的YAML配置字典。

        Returns:
            一个包含对比结果的字典，例如：
            {
                "success": bool,
                "error": Optional[str],
                "differences": {
                    "missing_in_help_args": [],
                    "missing_in_yaml_args": [],
                    "missing_in_help_opts": [],
                    "missing_in_yaml_opts": [],
                    "short_name_mismatches": []
                },
                "raw_llm_response": Optional[str]
            }
        """
        logger.debug(f"Starting comparison for command config: {cmd_config.get('name', 'unknown')}")

        # 1. 准备输入给LLM
        #    提取YAML配置中的关键信息 (arguments, options)
        expected_args = cmd_config.get("arguments", [])
        expected_opts = cmd_config.get("options", {})

        # 为了简化Prompt，可以只传递名称和简写
        simplified_args = [arg.get("name") for arg in expected_args if arg.get("name")]
        simplified_opts = {}
        for name, opt_cfg in expected_opts.items():
            simplified_opts[name] = opt_cfg.get("short")

        comparison_input = {"help_output": help_text, "expected_arguments": simplified_args, "expected_options": simplified_opts}

        # 将输入转换为字符串或保留为字典，取决于Prompt模板的设计
        # 暂时转换为JSON字符串以便清晰传递
        input_json_str = json.dumps(comparison_input, indent=2, ensure_ascii=False)

        # 2. 调用 LLMParser 进行解析/对比
        #    需要定义一个新的 content_type 和对应的 prompt 模板
        content_type = "command_help_comparison"

        logger.info(f"Calling LLMParser for {content_type}...")
        try:
            # parse 方法是同步的，内部处理了异步调用
            llm_result = self.llm_parser.parse(input_json_str, content_type=content_type)

            logger.debug(f"LLMParser raw result: {llm_result}")

            # 3. 处理LLM的响应
            if llm_result.get("success"):
                # 假设LLM被指示返回一个包含 "differences" 键的JSON字符串
                llm_response_content = llm_result.get("result")  # 或者 'content'，取决于LLMParser如何返回
                if not llm_response_content:
                    logger.error("LLMParser succeeded but returned no content/result.")
                    return {
                        "success": False,
                        "error": "LLM analysis succeeded but returned empty content.",
                        "differences": {},
                        "raw_llm_response": llm_result.get("raw_response"),
                    }

                try:
                    # 尝试解析LLM返回的内容为JSON
                    parsed_diff = json.loads(llm_response_content)

                    # 验证返回的结构是否符合预期
                    default_diff = {
                        "missing_in_help_args": [],
                        "missing_in_yaml_args": [],
                        "missing_in_help_opts": [],
                        "missing_in_yaml_opts": [],
                        "short_name_mismatches": [],
                    }
                    differences = parsed_diff.get("differences", default_diff)

                    # 基本的类型检查
                    for key in default_diff:
                        if key not in differences or not isinstance(differences[key], list):
                            logger.warning(f"LLM response missing or has invalid type for differences key: {key}. Using default.")
                            differences[key] = default_diff[key]

                    logger.info("Successfully parsed differences from LLM response.")
                    return {"success": True, "error": None, "differences": differences, "raw_llm_response": llm_result.get("raw_response")}
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response JSON: {e}. Response: {llm_response_content[:500]}...", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Failed to parse LLM response JSON: {e}",
                        "differences": {},
                        "raw_llm_response": llm_response_content,
                    }
                except Exception as e:
                    logger.error(f"Error processing LLM response content: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Error processing LLM response content: {e}",
                        "differences": {},
                        "raw_llm_response": llm_response_content,
                    }
            else:
                # LLMParser 本身失败
                logger.error(f"LLMParser failed: {llm_result.get('error')}")
                return {
                    "success": False,
                    "error": f"LLMParser failed: {llm_result.get('error')}",
                    "differences": {},
                    "raw_llm_response": llm_result.get("raw_response"),
                }

        except Exception as e:
            logger.error(f"Error during LLM comparison: {e}", exc_info=True)
            return {"success": False, "error": f"Error during LLM comparison: {e}", "differences": {}, "raw_llm_response": None}


# Example usage (for testing purposes)
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
#     # Mock LLM config if needed
#     config = {"provider": "openai", "api_key": "YOUR_API_KEY"}
#     processor = CommandHelpProcessor(config)

#     # Example help text and config
#     mock_help_text = """
#     Usage: mycli command [OPTIONS] ARG1 [ARG2]

#     Options:
#       -f, --force      Force operation.
#       --verbose        Enable verbose output.
#       -h, --help       Show this message and exit.
#       --extra-opt TEXT Extra option from help.
#     """
#     mock_cmd_config = {
#         "name": "mycli command",
#         "arguments": [{"name": "arg1"}, {"name": "arg_missing_in_help"}],
#         "options": {
#             "--force": {"short": "-f"},
#             "--verbose": {},
#             "--config": {"short": "-c"} # Missing in help
#         }
#     }

#     comparison_result = processor.compare(mock_help_text, mock_cmd_config)
#     print(json.dumps(comparison_result, indent=2, ensure_ascii=False))
