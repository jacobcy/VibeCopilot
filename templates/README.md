# VibeCopilot 模板系统

模板系统为VibeCopilot提供了可重用的内容模板，用于生成规则、命令、文档等各类资源。

## 功能概述

- **模板管理**：存储和检索模板
- **变量解析**：支持Jinja2变量语法
- **模板渲染**：将模板与变量结合生成内容
- **规则生成**：基于模板生成规则文件

## 目录结构

```
templates/
├── rule/           # 规则相关模板
│   ├── command.md  # 命令规则模板
│   └── ...
├── flow/           # 流程相关模板
├── doc/            # 文档相关模板
├── roadmap/        # 路线图相关模板
└── ...
```

## 模板格式

模板使用Markdown格式，包含YAML Front Matter和Jinja2模板语法：

```markdown
---
description: 模板描述
variables:
  - name: variable_name
    description: 变量描述
    required: true
    type: string
---

# 模板标题 {{ variable_name }}

这是模板内容，支持 {{ another_variable }} 变量替换。

{% if condition_variable %}
条件内容
{% endif %}

{% for item in list_variable %}
- {{ item }}
{% endfor %}
```

## 变量替换

模板支持以下变量替换方式：

- 基本变量：`{{ variable_name }}`
- 条件语句：`{% if condition %} ... {% endif %}`
- 循环语句：`{% for item in items %} ... {% endfor %}`
- 过滤器：`{{ variable | filter }}`

## 命令行使用

你可以通过VibeCopilot CLI使用模板功能：

```bash
# 列出所有可用模板
python vibecopilot.py template list

# 查看特定模板详情
python vibecopilot.py template show template_id

# 使用模板生成内容
python vibecopilot.py template generate template_id output.md --vars '{"name":"value"}'
```

## 辅助脚本

为简化模板生成，我们提供了一个辅助脚本：

```bash
# 使用辅助脚本生成模板
python generate_template.py template_id output_file.md '{"variable1":"value1","variable2":"value2"}'

# 示例：生成命令模板
python generate_template.py template_956c81b4 my_command.md '{"name":"测试命令", "description":"描述", "command":"test", "parameters": [{"name":"option", "description":"选项说明", "required":true}], "example":"/test --option=value", "notes":"注意事项"}'
```

## 在代码中使用模板

```python
# 直接使用模板系统
from src.db import get_session_factory
from src.templates.core.template_manager import TemplateManager
from src.templates.generators import RegexTemplateGenerator

# 创建会话和模板管理器
session_factory = get_session_factory()
session = session_factory()
template_manager = TemplateManager(session)

# 获取模板和设置变量
template = template_manager.get_template("template_956c81b4")
variables = {
    "name": "测试命令",
    "description": "命令描述",
    "command": "test",
    "parameters": [
        {"name": "option", "description": "选项说明", "required": True}
    ],
    "example": "/test --option=value",
    "notes": "使用注意事项"
}

# 生成内容
generator = RegexTemplateGenerator()
content = generator.generate(template, variables)

# 保存内容
with open("output.md", "w", encoding="utf-8") as f:
    f.write(content)
```

## 创建新模板

1. 在适当的子目录中创建`.md`文件
2. 添加YAML Front Matter定义元数据和变量
3. 使用Jinja2语法编写模板内容
4. 使用`template import`命令导入数据库（可选）

```bash
python vibecopilot.py template import path/to/new_template.md
```

## 模板变量类型

模板支持以下变量类型：

- `string`: 字符串
- `number`: 数字
- `boolean`: 布尔值
- `array`: 数组
- `object`: 对象

数组和对象类型可用于构建复杂的模板，例如参数列表：

```json
{
  "parameters": [
    {"name": "option1", "description": "第一个选项", "required": true},
    {"name": "option2", "description": "第二个选项", "required": false}
  ]
}
```

在模板中可以这样使用：

```
{% for param in parameters %}
- `{{param.name}}`: {{param.description}}{% if param.required %} (必填){% endif %}
{% endfor %}
```
