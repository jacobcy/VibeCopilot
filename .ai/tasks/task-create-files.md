---
id: create-files
story_id: example-story
title: 创建示例文件
description: 创建符合平铺结构的示例文件
status: todo
priority: medium
created_at: 2023-04-02
updated_at: 2023-04-02
assigned_to: developer
estimated_hours: 1
actual_hours: 0
---

# Task: 创建示例文件

## 描述

创建符合平铺结构的示例文件，包括epic、story和task文件。

## 实现细节

1. 创建epic-example.md文件，确保包含id、title等字段
2. 创建story-example.md文件，确保包含id、epic_id、tasks等字段
3. 创建task相关文件，确保包含id、story_id等字段
4. 确保所有文件都符合模板规范

## 完成标准

- epic示例文件已创建并包含必要字段
- story示例文件已创建并包含必要字段
- task示例文件已创建并包含必要字段
- 所有文件字段与模板保持一致

## 技术文档

参考`.cursor/templates/agile/`目录下的模板文件

## 注意事项

确保字段命名与模板一致，如使用id而非epic_id/story_id/task_id作为自身标识符

## 变更历史

- 2023-04-02: 创建任务
