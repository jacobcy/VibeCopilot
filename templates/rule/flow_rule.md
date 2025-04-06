---
description: {{ description }}
globs: {{ globs|default([]) }}
alwaysApply: {{ always_apply|default(false) }}
---

# VibeCopilot {{ flow_name }}规范

## 流程定位

本规则位于VibeCopilot核心开发流程的{{ flow_position }}阶段：
{% for phase in workflow_phases %}
{% if phase.current %}
{{ loop.index }}. →→ **当前阶段：{{ phase.name }}** ←←
{% else %}
{{ loop.index }}. {{ phase.name }}
{% endif %}
{% endfor %}

## {{ flow_name }}前置条件

{% for condition in preconditions %}

- {{ condition }}
{% endfor %}

## 关键规则

{% for rule_group in rule_groups %}

### {{ rule_group.name }}

{% for rule in rule_group.rules %}

- {{ rule }}
{% endfor %}

{% endfor %}

## {{ flow_name }}过程规范

{% for process in processes %}

### {{ process.name }}

{% for step in process.steps %}

- {{ step }}
{% endfor %}

{% endfor %}

## 与开发生命周期的衔接

### {{ previous_phase }}衔接

{% for item in previous_integration %}

- {{ item }}
{% endfor %}

### 向{{ next_phase }}衔接

{% for item in next_integration %}

- {{ item }}
{% endfor %}

## 示例

<example>
  {{ good_example|safe }}
</example>

<example type="invalid">
  {{ bad_example|safe }}
</example>
