---
id: example-story
epic_id: example-epic
title: 示例Story文件
description: 验证目录结构与模板一致性
status: draft
priority: medium
created_at: 2023-04-02
updated_at: 2023-04-02
assigned_to: developer
tasks:
  - create-dirs
  - create-files
progress: 20
---

# Story: 示例Story文件

## 用户故事

作为开发者，我希望采用平铺的.ai目录结构，以便与原版规则保持一致并降低复杂度。

## 验收标准

- .ai目录下包含prd、architecture、epics、stories、tasks等子目录
- 目录结构采用平铺方式，易于理解和访问
- 所有附加规则与原版规则目录使用一致

## 技术要点

- 确保创建了所有必要的子目录
- 文件命名清晰，如epic-xxx.md, story-xxx.md
- 通过文件内容frontmatter维护关联关系

## 依赖关系

无

## 变更历史

- 2023-04-02: 创建Story
