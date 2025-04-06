---
description: {{ description }}
globs: {{ globs }}
alwaysApply: true
---

# {{ title }}

## 自动规则说明

本规则将自动应用于匹配 `{{ globs|join(', ') }}` 的文件，无需用户明确调用。

## 目的

{{ purpose }}

## 应用方式

{{ application_method }}

## 自动处理逻辑

{% for logic in auto_logic %}

- {{ logic }}
{% endfor %}

## 预期影响

{{ expected_impact }}
