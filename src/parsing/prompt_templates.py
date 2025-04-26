"""
提示模板模块

提供各种内容类型的提示模板。
"""

from typing import Dict

# 提示模板字典
_PROMPT_TEMPLATES = {
    "workflow": """请分析以下规则文档中定义的工作流程。规则内容如下：

{content}

请提取工作流的阶段（stages）和转换关系（transitions）信息，并严格按照以下有效的JSON结构返回。**你的回答必须只包含一个JSON对象，不包含任何注释、标记、代码块指示符（例如 ```json）或任何其他解释性文本。**

JSON结构模板：
{{
    "stages": [
        {{
            "id": "stage_id",
            "name": "阶段名称",
            "description": "阶段详细描述",
            "checklist": [
                "检查项1",
                "检查项2"
            ],
            "deliverables": [
                "交付物1",
                "交付物2"
            ]
        }}
        // 可以有更多 stages 对象
    ],
    "transitions": [
        {{
            "id": "transition_id",
            "from_stage": "源阶段id",
            "to_stage": "目标阶段id",
            "condition": "转换条件",
            "description": "转换的详细描述"
        }}
        // 可以有更多 transitions 对象
    ]
}}

请确保：
1. 所有ID都是唯一的。
2. 阶段之间的转换关系完整且合理。
3. 检查项和交付物具体且可操作。
4. 最终输出是一个语法完全正确的JSON对象。
""",
    "rule": """
Parse the following rule content and extract its structured information.
Return the result as JSON.

Rule content:
{content}
""",
    "document": """
Parse the following document content and extract its structured information.
Return the result as JSON with the following structure:
{{
    "title": "文档标题",
    "structure": {{
        "headings": [
            {{
                "level": 1,
                "text": "一级标题"
            }},
            {{
                "level": 2,
                "text": "二级标题"
            }}
        ]
    }},
    "summary": "文档内容摘要",
    "toc": [
        {{
            "level": 1,
            "text": "一级标题",
            "children": [
                {{
                    "level": 2,
                    "text": "二级标题",
                    "children": []
                }}
            ]
        }}
    ],
    "metadata": {{
        "word_count": 100,
        "line_count": 20
    }}
}}

Document content:
{content}
""",
    "generic": """
Parse the following content and extract its key information.
Return the result as JSON.

Content:
{content}
""",
    "code": """
Analyze the following code and extract its key components and functionality.
Return the result as JSON.

Code:
{content}
""",
    "roadmap": """
请分析以下路线图YAML内容，将其解析为规范的epic-story-task结构。

路线图内容:
{content}

返回一个JSON对象，结构如下:
{{
  "metadata": {{
    "title": "路线图标题",
    "description": "路线图描述",
    "version": "版本号",
    "last_updated": "最后更新日期(YYYY-MM-DD)"
  }},
  "epics": [
    {{
      "title": "史诗标题",
      "description": "史诗描述",
      "status": "状态(只能是 'todo', 'in_progress', 'done', 或 'completed')",
      "stories": [
        {{
          "title": "故事标题",
          "description": "故事描述",
          "status": "状态(只能是 'todo', 'in_progress', 'done', 或 'completed')",
          "tasks": [
            {{
              "title": "任务标题",
              "description": "任务描述",
              "status": "状态(只能是 'todo', 'in_progress', 'done', 或 'completed')",
              "priority": "优先级(low/medium/high/critical)",
              "assignees": ["负责人"],
              "due_date": "截止日期(YYYY-MM-DD)"
            }}
          ]
        }}
      ]
    }}
  ]
}}

重要要求:
1. 如果输入包含milestone结构，将其转换为epic-story结构，每个milestone对应一个story
2. 如果输入包含tasks结构，确保任务被正确放入对应的story中
3. 确保priority字段使用标准值: low, medium, high, critical(不要使用P0, P1等格式)
4. 日期格式必须为YYYY-MM-DD
5. 保持原有标识符(id)不变
6. 如果缺少必要字段，使用合理的默认值
7. 只返回JSON结果，不要包含任何解释性文本
""",
    "command_help_comparison": """
Please compare the command's help output with its expected configuration provided below and report the differences strictly in the specified JSON format.

Input Data:
{content}
""",
}

# 系统提示字典
_SYSTEM_PROMPTS = {
    "workflow": """你是一个专业的工作流分析专家，任务是将规则文档转换为结构化的JSON。请严格遵循用户提示中要求的JSON格式，只输出JSON对象，不包含任何额外的文本、注释或标记。""",
    "roadmap": """你是一个专业的路线图结构化专家。你的任务是：
1. 仔细分析提供的路线图YAML内容
2. 将内容转换为标准的epic-story-task结构
3. 确保所有字段名和值符合标准格式
4. 特别注意将milestone结构转换为epic-story结构
5. 确保priority字段使用标准值(low, medium, high, critical)
6. 将结果以JSON格式返回，不要包含任何解释性文本
7. 确保输出的JSON格式完全符合要求的结构""",
    "document": """你是一个专业的文档分析专家。你的任务是：
1. 仔细分析提供的文档内容
2. 提取文档的标题、结构和主要内容
3. 生成文档的摘要和目录结构
4. 计算基本的文档统计信息
5. 将结果以JSON格式返回，确保包含所有必要字段""",
    "rule": """你是一个专业的规则分析专家。你的任务是：
1. 仔细分析提供的规则文档
2. 提取规则的标题、类型和主要内容
3. 识别规则中的条件、触发器和动作
4. 将规则进行结构化并以JSON格式返回
5. 确保输出格式严格符合要求""",
    "code": """你是一个专业的代码分析专家。你的任务是：
1. 仔细分析提供的代码内容
2. 识别代码的主要组件、函数和类
3. 理解代码的流程和功能
4. 将分析结果以JSON格式返回
5. 包含代码的结构、功能说明和关键点""",
    "generic": "You are a helpful assistant that parses content accurately.",
    "command_help_comparison": """You are an expert command-line interface (CLI) tool analyst. Your task is to compare a command's actual `--help` output with its expected configuration (arguments and options) provided in the user message JSON.

Analyze the `help_output` text against the `expected_arguments` list and `expected_options` dictionary. Identify the following types of differences:

1.  **Missing Arguments in Help:** Arguments listed in `expected_arguments` but not found in the `help_output` (usually in the 'Usage:' line).
2.  **Extra Arguments in Help:** Arguments found in the `help_output`'s 'Usage:' line (typically uppercase words, excluding 'OPTIONS') but not listed in `expected_arguments`.
3.  **Missing Options in Help:** Options (long form, e.g., `--option`) listed as keys in `expected_options` but not found in the `help_output`'s 'Options:' section.
4.  **Extra Options in Help:** Options (long form, e.g., `--option`) found in the `help_output`'s 'Options:' section but not listed as keys in `expected_options`. Ignore the implicit '--help' option found in help text unless it's explicitly in `expected_options`.
5.  **Short Name Mismatches:** Options where the short name (e.g., '-f') found in the `help_output` differs from the value specified in `expected_options` for that long option. Include cases where one source provides a short name and the other doesn't (use `null` for missing short names).

You MUST return ONLY a single valid JSON object containing the identified differences. The JSON object must have a single top-level key "differences". The value of "differences" must be an object with the following keys, each holding a list:
- `missing_in_help_args`: List of argument name strings.
- `missing_in_yaml_args`: List of argument name strings.
- `missing_in_help_opts`: List of option name strings (long form).
- `missing_in_yaml_opts`: List of option name strings (long form).
- `short_name_mismatches`: List of objects, each with keys: `option` (string, long form), `yaml_short` (string or null), `help_short` (string or null).

Return empty lists `[]` for categories with no differences. Do NOT add any explanations, comments, or introductory text outside the JSON object.""",
}


def get_prompt_template(content_type: str) -> str:
    """
    获取指定内容类型的提示模板

    Args:
        content_type: 内容类型，如'rule'、'document'等

    Returns:
        提示模板字符串
    """
    return _PROMPT_TEMPLATES.get(content_type, _PROMPT_TEMPLATES["generic"])


def get_system_prompt(content_type: str) -> str:
    """
    获取指定内容类型的系统提示

    Args:
        content_type: 内容类型，如'rule'、'document'等

    Returns:
        系统提示字符串
    """
    return _SYSTEM_PROMPTS.get(content_type, _SYSTEM_PROMPTS["generic"])


def add_prompt_template(content_type: str, template: str) -> None:
    """
    添加或更新提示模板

    Args:
        content_type: 内容类型
        template: 提示模板字符串
    """
    _PROMPT_TEMPLATES[content_type] = template


def add_system_prompt(content_type: str, prompt: str) -> None:
    """
    添加或更新系统提示

    Args:
        content_type: 内容类型
        prompt: 系统提示字符串
    """
    _SYSTEM_PROMPTS[content_type] = prompt


def get_all_prompt_templates() -> Dict[str, str]:
    """
    获取所有提示模板

    Returns:
        提示模板字典
    """
    return _PROMPT_TEMPLATES.copy()


def get_all_system_prompts() -> Dict[str, str]:
    """
    获取所有系统提示

    Returns:
        系统提示字典
    """
    return _SYSTEM_PROMPTS.copy()
