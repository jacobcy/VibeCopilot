---
description: {{ description }}
globs: {{ globs|default(["*.py"]) }}
alwaysApply: {{ always_apply|default(false) }}
---

# {{ title }}

## 规则目的

{{ purpose }}

## 应用场景

{% for scenario in scenarios %}

- {{ scenario }}
{% endfor %}

## 关键规则

{% for rule in key_rules %}

### {{ rule.name }}

{{ rule.description }}

{% if rule.examples %}
**示例**:
```
{{ rule.examples }}
```
{% endif %}

{% endfor %}

## 示例

<example>
  {{ good_example }}
</example>

<example type="invalid">
  {{ bad_example }}
</example>
