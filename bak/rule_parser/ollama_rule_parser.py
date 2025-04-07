"""
Ollama规则解析器
使用Ollama服务解析规则文件，作为OpenAI的备选
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from adapters.rule_parser.base_parser import RuleParser
from adapters.rule_parser.lib.rule_template import extract_blocks_from_content, validate_rule_structure


class OllamaRuleParser(RuleParser):
    """Ollama规则解析器"""

    def __init__(self, model: str = "mistral"):
        """初始化解析器

        Args:
            model: 使用的Ollama模型
        """
        super().__init__(model)

    def parse_rule_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """使用Ollama解析规则内容

        Args:
            content: 规则文本内容
            context: 上下文信息(文件路径等)

        Returns:
            Dict: 解析后的规则结构
        """
        # 构建提示词
        prompt = self._build_prompt(context, content)

        # 调用Ollama
        try:
            result = subprocess.run(["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True)

            # 提取JSON部分
            output = result.stdout.strip()
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
                            blocks = extract_blocks_from_content(content)
                            if blocks:
                                parsed_json["items"] = [
                                    {
                                        "content": block["content"],
                                        "category": block["type"],
                                        "id": block["id"],
                                    }
                                    for block in blocks
                                ]

                        return parsed_json
                    else:
                        return self._get_default_result(context)

                except json.JSONDecodeError as e:
                    print(f"解析JSON失败: {e}")
                    print(f"原始JSON字符串: {json_str}")
                    return self._get_default_result(context)
            else:
                print(f"无法从输出中提取JSON: {output}")
                return self._get_default_result(context)

        except subprocess.CalledProcessError as e:
            print(f"调用Ollama失败: {e}")
            print(f"错误输出: {e.stderr}")
            return self._get_default_result(context)
        except FileNotFoundError:
            print("Ollama命令不可用，请确保已安装Ollama并添加到PATH中")
            return self._get_default_result(context)

    def _build_prompt(self, file_path: str, content: str) -> str:
        """构建Ollama提示词

        Args:
            file_path: 规则文件路径
            content: 规则内容

        Returns:
            str: 提示词
        """
        return f"""解析以下Markdown格式的规则文件，提取其结构和组件。

规则文件路径: {file_path}

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
  ],
  "content": "原始规则内容"
}}

只返回JSON，不要有其他文本。如果无法确定某个字段的值，使用合理的默认值。"""
