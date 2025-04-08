---
title: 示例模板
description: 这是一个示例模板，用于测试模板系统
type: example
author: VibeCopilot
version: 1.0.0
tags:
  - test
  - example
---

# 示例模板

这是一个示例模板的内容，用于演示模板系统的功能。

## 变量示例

- 姓名: {{ name }}
- 日期: {{ date }}
- 列表:
{% for item in items %}
  - {{ item }}
{% endfor %}

## 条件示例

{% if show_section %}
这个部分只有在show_section为真时才会显示。
{% endif %}

## 结束

这是模板的结尾。
