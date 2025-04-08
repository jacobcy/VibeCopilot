---
description: 默认文档模板，用于创建基础文档
variables:
  - name: title
    description: 文档标题
    required: true
    type: string
  - name: description
    description: 文档描述
    required: true
    type: string
  - name: category
    description: 文档分类
    required: false
    type: string
    default: "一般文档"
  - name: date
    description: 创建/更新日期
    required: false
    type: string
    default: "{{current_date}}"
type: doc
author: VibeCopilot
version: 1.0.0
tags:
  - documentation
  - general
---

# {{title}}

## 概述

{{description}}

## 内容

## 相关文档

## 参考资料
