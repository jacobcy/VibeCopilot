"""
文档解析模块

提供解析文档内容的函数，使用 Ollama 服务解析 Markdown 格式的文档
"""

import json
import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_document(content: str, context: str, model: str = "mistral") -> Dict[str, Any]:
    """解析文档内容

    Args:
        content: 文档文本内容
        context: 上下文信息(文件路径等)
        model: 使用的 Ollama 模型

    Returns:
        Dict: 解析后的文档结构
    """
    logger.info(f"使用Ollama解析文档内容: {context}")

    # 构建提示词
    prompt = f"""解析以下Markdown格式的文档，提取其结构和组件。

文档文件路径: {context}

文档内容:
{content}

请分析这个文档并提取以下信息:
1. 文档ID（通常是文件名，如没有明确定义）
2. 文档标题（通常在一级标题中）
3. 文档描述（概述文档的目的）
4. 文档分块（基于标题层级）

以严格JSON格式返回结果:
{{
  "id": "文档ID",
  "title": "文档标题",
  "description": "文档描述",
  "blocks": [
    {{
      "id": "块ID",
      "type": "heading|text|code|list|quote",
      "level": 1-6,  // 仅用于heading类型
      "content": "块内容",
      "language": "编程语言"  // 仅用于code类型
    }}
  ]
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""

    # 调用Ollama API
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt], capture_output=True, text=True, check=True
        )

        # 提取JSON部分
        return extract_json_from_output(result.stdout, content, context)

    except subprocess.CalledProcessError as e:
        logger.error(f"调用Ollama失败: {e}")
        logger.debug(f"错误输出: {e.stderr}")
        return get_default_document_result(context)
    except FileNotFoundError:
        logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
        return get_default_document_result(context)


def get_default_document_result(context: str) -> Dict[str, Any]:
    """获取默认的文档解析结果

    Args:
        context: 上下文信息(文件路径等)

    Returns:
        Dict: 默认文档结构
    """
    return {
        "id": context.split("/")[-1].split(".")[0] if context else "unknown",
        "title": "未解析文档",
        "description": "解析失败时创建的默认文档",
        "blocks": [],
        "path": context,
    }


def extract_json_from_output(output: str, content: str, context: str) -> Dict[str, Any]:
    """从Ollama输出中提取JSON数据

    Args:
        output: Ollama的输出文本
        content: 原始文档内容
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
            if validate_document_structure(parsed_json):
                return parsed_json
            else:
                logger.warning(f"解析后的文档结构无效: {json_str}")
                return get_default_document_result(context)

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            logger.debug(f"原始JSON字符串: {json_str}")
            return get_default_document_result(context)
    else:
        logger.error(f"无法从输出中提取JSON: {output}")
        return get_default_document_result(context)


def validate_document_structure(document_data: Dict[str, Any]) -> bool:
    """验证文档数据结构

    Args:
        document_data: 文档数据

    Returns:
        bool: 是否为有效的文档结构
    """
    required_fields = ["id", "title", "blocks"]
    if not all(field in document_data for field in required_fields):
        return False

    # 验证块结构
    blocks = document_data.get("blocks", [])
    if not isinstance(blocks, list):
        return False

    for block in blocks:
        if not isinstance(block, dict):
            return False
        if "type" not in block or "content" not in block:
            return False

    return True
