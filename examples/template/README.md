# VibeCopilot 模板系统示例

本目录包含了VibeCopilot模板系统的示例文件，展示如何使用模板系统创建和生成内容。

## 文件列表

1. **generate_template.py** - 命令行工具，用于从数据库中获取模板并生成内容
2. **test_template_rule_generator_simple.py** - 基于文件的简易模板渲染器，不依赖数据库
3. **test_template_gen.py** - 测试模板生成的脚本，直接调用handler
4. **sample_template.md** - 示例模板文件，包含Front Matter和模板内容
5. **test_validation.py** - 验证器模块的测试脚本，用于验证规则和模板

## 使用方法

### 使用命令行工具生成模板

```bash
# 使用数据库中的模板生成内容
python generate_template.py template_956c81b4 output.md '{"name":"测试命令", "description":"描述"}'
```

### 使用简易生成器

```bash
# 从文件模板生成内容
python test_template_rule_generator_simple.py sample_template.md output.md --vars='{"name":"测试命令"}'
```

### 运行直接测试

```bash
# 直接测试模板生成
python test_template_gen.py
```

## 模板语法

模板使用Jinja2语法，支持变量替换、条件和循环等功能：

```markdown
# {{ name }} 命令

## 描述
{{ description }}

{% if parameters %}
## 参数
{% for param in parameters %}
- `{{ param.name }}`: {{ param.description }}{% if param.required %} (必填){% endif %}
{% endfor %}
{% endif %}
```

## 更多信息

详情请参考 [模板系统文档](/templates/README.md)
