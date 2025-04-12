"""
提示模板模块

提供各种内容类型的提示模板。
"""

from typing import Dict

# 提示模板字典
_PROMPT_TEMPLATES = {
    "workflow": """请分析以下规则文档中定义的工作流程。规则内容如下：

{content}

请提取以下信息并以JSON格式返回：
1. 工作流的各个阶段（stages）：
   - 每个阶段的ID、名称和描述
   - 每个阶段的检查项（checklist）
   - 每个阶段的交付物（deliverables）

2. 阶段之间的转换关系（transitions）：
   - 转换的源阶段和目标阶段
   - 转换的触发条件
   - 转换的描述

请严格按照以下JSON结构返回：
{{
    "stages": [
        {{
            "id": "stage_id",            // 阶段唯一标识
            "name": "阶段名称",           // 阶段名称
            "description": "阶段描述",    // 阶段详细描述
            "checklist": [               // 检查项列表
                "检查项1",
                "检查项2"
            ],
            "deliverables": [           // 交付物列表
                "交付物1",
                "交付物2"
            ]
        }}
    ],
    "transitions": [
        {{
            "id": "transition_id",       // 转换唯一标识
            "from_stage": "源阶段id",     // 源阶段ID
            "to_stage": "目标阶段id",     // 目标阶段ID
            "condition": "转换条件",      // 触发条件
            "description": "转换描述"     // 转换的详细描述
        }}
    ]
}}

注意：
1. 确保所有ID都是唯一的
2. 阶段之间的转换关系要完整且合理
3. 检查项和交付物要具体且可操作
4. 所有字段都必须填写，不要省略任何必要信息
""",
    "rule": """
Parse the following rule content and extract its structured information.
Return the result as JSON.

Rule content:
{content}
""",
    "document": """
Parse the following document content and extract its structured information.
Return the result as JSON.

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
      "status": "状态(planned/in_progress/completed)",
      "stories": [
        {{
          "title": "故事标题",
          "description": "故事描述",
          "status": "状态(planned/in_progress/completed)",
          "tasks": [
            {{
              "title": "任务标题",
              "description": "任务描述",
              "status": "状态(planned/in_progress/completed)",
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


def add_prompt_template(content_type: str, template: str) -> None:
    """
    添加或更新提示模板

    Args:
        content_type: 内容类型
        template: 提示模板字符串
    """
    _PROMPT_TEMPLATES[content_type] = template


def get_all_prompt_templates() -> Dict[str, str]:
    """
    获取所有提示模板

    Returns:
        提示模板字典
    """
    return _PROMPT_TEMPLATES.copy()
