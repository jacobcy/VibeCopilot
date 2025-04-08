---
description: 教程文档模板，用于创建教程文档
variables:
  - name: title
    description: 教程标题
    required: true
    type: string
  - name: description
    description: 教程描述
    required: true
    type: string
  - name: date
    description: 创建/更新日期
    required: false
    type: string
    default: "{{current_date}}"
  - name: prerequisites
    description: 前提条件列表
    required: false
    type: array
    default: []
type: doc
author: VibeCopilot
version: 1.0.0
tags:
  - tutorial
  - documentation
  - learning
---

# {{title}} 教程

## 简介

{{description}}

## 前提条件

{% if prerequisites %}
{% for item in prerequisites %}

- {{item}}
{% endfor %}
{% else %}
- 前提条件1
- 前提条件2
{% endif %}

## 步骤

### 步骤1: 开始

### 步骤2: 配置

### 步骤3: 运行

## 常见问题

## 进阶用法

## 相关资源
