---
title: 示例架构文档
id: arch-example-001
status: draft
related_prd: prd-example-001
created_at: 2023-04-02
---

# 示例架构文档

## 概述

此架构文档定义了项目的目录结构统一标准，确保所有规则引用的目录结构保持一致。

## 目录结构设计

```
项目根目录/
├── .ai/                # AI工具相关数据
│   ├── architecture/   # 架构文档（原版规则一致）
│   ├── cache/          # 命令缓存目录
│   ├── epics/          # 详细Epic-Story-Task结构
│   │   └── [epic-id]/
│   │       ├── epic.md
│   │       └── stories/
│   │           └── [story-id]/
│   │               ├── story.md
│   │               └── tasks/
│   │                   └── [task-id].md
│   ├── knowledge_graph/ # 知识图谱
│   ├── logs/           # 开发日志
│   ├── prd/            # PRD文档（原版规则一致）
│   ├── stories/        # 故事摘要（原版规则一致）
│   ├── prd.md          # 主PRD链接（兼容原版规则）
│   └── arch.md         # 主架构文档链接（兼容原版规则）
└── docs/               # 项目文档（保留以备档）
    ├── prd/            # PRD备份位置
    └── architecture/   # 架构文档备份位置
```

## 兼容性设计

1. **原版规则兼容性**
   - 保持原版规则使用的`.ai/prd/`和`.ai/architecture/`目录
   - 提供根目录下的prd.md和arch.md文件以兼容简单引用
   - 在`.ai/stories/`目录中保存故事摘要

2. **附加规则功能性**
   - 保留Epic-Story-Task结构以支持详细的敏捷开发流程
   - 通过自动生成摘要保持两套系统的内容同步

## 技术实现注意事项

1. 所有工具和命令需同时更新两套目录结构
2. 主数据存储在Epic-Story-Task结构中
3. 在`.ai/stories/`中存储摘要或引用
