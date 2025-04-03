# 规则模板引擎 - 用户指南

## 概述

规则模板引擎是一个用于生成规范化规则文件的工具，通过预定义的模板和变量值快速创建符合项目要求的规则。它能帮助开发者减少规则创建的重复工作，确保规则质量和一致性。

## 主要功能

### 1. 使用模板创建规则

```python
from src.rule_templates.core.template_engine import TemplateEngine
from src.rule_templates.core.rule_generator import RuleGenerator
from src.rule_templates.core.template_manager import TemplateManager

# 初始化组件
template_manager = TemplateManager(templates_dir="/path/to/templates")
template_engine = TemplateEngine()
rule_generator = RuleGenerator(template_engine=template_engine)

# 加载模板
template_manager.load_templates_from_directory()
template = template_manager.get_template("cmd-rule")

# 设置变量值
variables = {
    "title": "我的命令规则",
    "description": "这是一个示例命令规则",
    "command": "example",
    "purpose": "用于演示模板引擎功能",
    "format": "/example [参数]",
    "examples": ["示例1", "示例2"]
}

# 生成规则文件
rule = rule_generator.generate_rule_file(
    template,
    variables,
    output_path="/path/to/rules/example-cmd.md"
)
```

### 2. 管理模板

```python
# 获取所有模板
templates = template_manager.get_all_templates()

# 按类型搜索模板
cmd_templates = template_manager.search_templates(type="cmd")

# 添加新模板
new_template = Template(
    name="新模板",
    description="一个新的模板",
    type="flow",
    content="模板内容...",
    variables=[...]
)
template_manager.add_template(new_template)

# 更新模板
template_manager.update_template(
    "template-id",
    {"description": "更新的描述"}
)

# 删除模板
template_manager.delete_template("template-id")
```

### 3. 批量生成规则

```python
# 批量生成规则
template_configs = [
    {
        "template": template1,
        "variables": variables1,
        "output_file": "rule1.md"
    },
    {
        "template": template2,
        "variables": variables2,
        "output_file": "rule2.md"
    }
]

rules = rule_generator.batch_generate_rules(
    template_configs,
    base_output_dir="/path/to/output"
)
```

## 常见问题

### 模板变量错误

**问题**: 在渲染模板时出现变量验证错误

**解决方案**: 确保提供所有必填变量。检查变量类型是否正确，例如数组类型变量必须提供列表值。

```python
# 错误的变量值
variables = {
    "title": "标题",
    # 缺少必填变量"description"
    "scenes": "这不是数组" # 应该是列表类型
}

# 正确的变量值
variables = {
    "title": "标题",
    "description": "描述",
    "scenes": ["场景1", "场景2"] # 正确的列表类型
}
```

### 模板语法错误

**问题**: 模板内容包含语法错误

**解决方案**: 检查模板内容的Jinja2语法，确保所有标签正确闭合，变量名拼写正确。

```
# 错误的模板语法
{{ 未闭合的标签

# 正确的模板语法
{{ variable }}
{% for item in items %}
  - {{ item }}
{% endfor %}
```

### 输出路径不存在

**问题**: 生成规则文件时提示路径不存在

**解决方案**: 规则生成器会自动创建目录结构，但请确保提供有效的路径，且程序有写入权限。

## 注意事项

1. 模板内容支持完整的Jinja2语法，包括条件语句、循环、过滤器等
2. 规则ID自动从规则名称生成，采用kebab-case格式
3. 默认支持camel_case、pascal_case和kebab_case过滤器转换变量格式
4. 模板加载后会缓存在内存中，修改模板文件后需要调用`reload_templates()`刷新

## 进阶用法

### 自定义模板加载器

```python
# 创建自定义模板加载器
class MongoTemplateLoader:
    def load_templates(self):
        # 从MongoDB加载模板的实现...
        pass

# 使用自定义加载器
template_manager = TemplateManager(custom_loader=MongoTemplateLoader())
```

### 自定义模板过滤器

```python
# 向模板引擎添加自定义过滤器
template_engine = TemplateEngine()
template_engine.env.filters['my_filter'] = lambda x: x.upper() + '!'
```
