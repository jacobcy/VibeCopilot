"""
通用内容解析模块

提供解析通用内容的函数，使用 Ollama 服务解析各种格式的文本内容
"""

import json
import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_generic(content: str, context: str, model: str = "mistral") -> Dict[str, Any]:
    """解析通用内容

    Args:
        content: 文本内容
        context: 上下文信息(文件路径等)
        model: 使用的 Ollama 模型

    Returns:
        Dict: 解析后的结构
    """
    logger.info(f"使用Ollama解析通用内容: {context}")

    # 构建提示词
    prompt = f"""分析以下内容，提取关键信息并生成结构化数据。

文件路径: {context}

内容:
{content}

请分析这个内容并提取以下信息:
1. 标题或主题
2. 内容摘要或简短描述
3. 关键信息点
4. 结构化的主要内容区块

以严格JSON格式返回结果:
{{
  "title": "内容的标题或主题",
  "summary": "内容摘要或简短描述",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "sections": [
    {{
      "heading": "第一部分标题",
      "content": "第一部分内容"
    }},
    {{
      "heading": "第二部分标题",
      "content": "第二部分内容"
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
        return get_default_generic_result(context, content)
    except FileNotFoundError:
        logger.error("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
        return get_default_generic_result(context, content)


def get_default_generic_result(context: str, content: str) -> Dict[str, Any]:
    """获取默认的通用解析结果

    Args:
        context: 上下文信息(文件路径等)
        content: 原始内容

    Returns:
        Dict: 默认结构
    """
    # 尝试提取标题 (first line or first h1)
    lines = content.splitlines()
    title = "未解析内容"

    if lines:
        title = lines[0].strip("#").strip()

    # 尝试生成摘要 (first 100 chars)
    summary = content[:100] + "..." if len(content) > 100 else content

    return {
        "id": context.split("/")[-1].split(".")[0] if context else "unknown",
        "title": title,
        "summary": summary,
        "key_points": [],
        "sections": [],
        "content": content,
        "path": context,
    }


def extract_json_from_output(output: str, content: str, context: str) -> Dict[str, Any]:
    """从Ollama输出中提取JSON数据

    Args:
        output: Ollama的输出文本
        content: 原始内容
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

            # 添加ID字段
            if "id" not in parsed_json and context:
                parsed_json["id"] = context.split("/")[-1].split(".")[0]

            # 添加原始内容
            if "content" not in parsed_json:
                parsed_json["content"] = content

            # 添加路径信息
            if "path" not in parsed_json:
                parsed_json["path"] = context

            return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            logger.debug(f"原始JSON字符串: {json_str}")
            return get_default_generic_result(context, content)
    else:
        logger.error(f"无法从输出中提取JSON: {output}")
        return get_default_generic_result(context, content)
