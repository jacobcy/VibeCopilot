---
description: 当用户输入/{{ command_name }}命令时，{{ description }}
globs:
alwaysApply: false
---

# VibeCopilot {{ command_title }}命令处理器

## 命令目的

`/{{ command_name }}`命令用于{{ purpose }}

## 规则关系

本命令规则与其他规则紧密配合：
{% for relation in relations %}

- `{{ relation.rule }}`：{{ relation.description }}
{% endfor %}

## 依赖关系

{% for dependency in dependencies %}

- {{ dependency }}
{% endfor %}

## 命令格式规范

基本语法: `/{{ command_name }} [参数]`

参数说明:
{% for param in parameters %}

- `{{ param.name }}`{% if param.required %}：**必选**{% else %}：可选{% endif %}，{{ param.description }}
{% endfor %}

## 命令执行流程

```mermaid
flowchart TD
    {{ flow_chart }}
```

## 命令管理功能

{% for feature in features %}

### {{ feature.name }}

{{ feature.description }}
```
{{ feature.example }}
```
{% endfor %}

## 命令注释用法

使用`{/{{ command_name }}}`格式表示提及命令而非执行：
```
讨论命令时，使用{/{{ command_name }}}表示提及命令而非执行，例如：
"关于{/{{ command_name }}}命令，它用于{{ purpose }}"
```

## 与其他命令的集成

{% for integration in integrations %}

- `/{{ integration.command }}`: {{ integration.description }}
{% endfor %}

## 示例

<example>
  用户: `/{{ command_name }} {{ example_command }}`

  系统响应:
  ```
  {{ example_response }}
  ```
</example>

<example type="invalid">
  用户: `/{{ command_name }} {{ invalid_example_command }}`

  系统响应:
  ```
  {{ invalid_example_response }}
  ```
</example>
