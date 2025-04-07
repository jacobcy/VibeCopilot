"""
规则解析模块

提供解析规则内容的函数，使用 Ollama 服务解析 Markdown 格式的规则文件
"""

import json
import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_rule(content: str, context: str, model: str = "mistral") -> Dict[str, Any]:
    """解析规则内容

    Args:
        content: 规则文本内容
        context: 上下文信息(文件路径等)
        model: 使用的 Ollama 模型

    Returns:
        Dict: 解析后的规则结构
    """
    logger.info(f"使用Ollama解析规则内容: {context}")

    # 构建提示词
    prompt = f"""解析以下Markdown格式的规则文件，提取其结构和组件。

规则文件路径: {context}

规则内容:
{content}

请分析这个规则文件并提取以下信息:
1. 规则ID（通常是文件名，如没有明确定义）
2. 规则名称
3. 规则类型（agent、auto、manual、always）
4. 规则描述
5. 适用的文件模式（globs）
6. 是否始终应用
7. 规则条目列表（内容、优先级和分类）
8. 示例列表（如果有）

以严格JSON格式返回结果:
{{
  "id": "规则ID（如未明确定义则使用文件名）",
  "name": "规则名称",
  "type": "规则类型",
  "description": "规则描述",
  "globs": ["适用的文件模式1", "适用的文件模式2"],
  "always_apply": true或false,
  "items": [
    {{
      "content": "规则条目内容",
      "priority": 优先级数值,
      "category": "条目分类"
    }}
  ],
  "examples": [
    {{
      "content": "示例内容",
      "is_valid": true或false,
      "description": "示例描述"
    }}
  ]
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""

    # 调用Ollama API
    try:
        result = subprocess.run(["ollama", "run", model, prompt], capture_output=True, text=True, check=True)

        # 提取JSON部分
        return extract_json_from_output(result.stdout, content, context)

    except subprocess.CalledProcessError as e:
        logger.error(f"调用Ollama失败: {e}")
        logger.debug(f"错误输出: {e.stderr}")
        return get_default_rule_result(context)
    except FileNotFoundError:
        logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
        return get_default_rule_result(context)


def get_default_rule_result(context: str) -> Dict[str, Any]:
    """获取默认的规则解析结果

    Args:
        context: 上下文信息(文件路径等)

    Returns:
        Dict: 默认规则结构
    """
    return {
        "id": context.split("/")[-1].split(".")[0] if context else "unknown",
        "name": "未解析规则",
        "type": "manual",
        "description": "解析失败时创建的默认规则",
        "globs": [],
        "always_apply": False,
        "items": [],
        "examples": [],
        "path": context,
    }


def extract_json_from_output(output: str, content: str, context: str) -> Dict[str, Any]:
    """从Ollama输出中提取JSON数据

    Args:
        output: Ollama的输出文本
        content: 原始规则内容
        context: 上下文信息(文件路径等)

    Returns:
        Dict: 解析后的JSON数据
    """
    # 提取JSON部分
    output = output.strip()
    json_start = output.find("{")
    json_end = output.rfind("}") + 1

    if json_start >= 0 and json_end > json_start:
        json_str = output[json_start:json_end]
        try:
            parsed_json = json.loads(json_str)

            # 添加原始内容
            if "content" not in parsed_json:
                parsed_json["content"] = content

            # 验证结果
            if validate_rule_structure(parsed_json):
                # 如果规则项为空，尝试从内容中提取块
                if not parsed_json.get("items"):
                    try:
                        from adapters.content_parser.lib.content_template import extract_blocks_from_content

                        blocks = extract_blocks_from_content(content)
                        if blocks:
                            parsed_json["items"] = [
                                {
                                    "content": block["content"],
                                    "category": block["type"],
                                    "id": block.get("id", f"block_{i}"),
                                }
                                for i, block in enumerate(blocks)
                            ]
                    except ImportError:
                        logger.warning("无法导入extract_blocks_from_content以提取块")

                return parsed_json
            else:
                logger.warning(f"解析后的规则结构无效: {json_str}")
                return get_default_rule_result(context)

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            logger.debug(f"原始JSON字符串: {json_str}")
            return get_default_rule_result(context)
    else:
        logger.error(f"无法从输出中提取JSON: {output}")
        return get_default_rule_result(context)


def validate_rule_structure(rule_data: Dict[str, Any]) -> bool:
    """验证规则数据结构

    Args:
        rule_data: 规则数据

    Returns:
        bool: 是否为有效的规则结构
    """
    try:
        # 导入验证函数
        from adapters.content_parser.lib.content_template import validate_rule_structure as lib_validate_rule

        return lib_validate_rule(rule_data)
    except ImportError:
        # 如果导入失败，进行基本验证
        required_fields = ["id", "name", "type", "description"]
        return all(field in rule_data for field in required_fields)
