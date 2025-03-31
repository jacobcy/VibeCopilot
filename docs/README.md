# VibeCopilot 文档结构

本项目采用混合文档结构，按照主要受众和功能分类组织文档。

## 文档目录结构

```
docs/
├── ai/          # AI专用文档
│   ├── prompts/ # 提示词模板
│   ├── context/ # 上下文信息
│   ├── rules/   # AI行为规则
│   └── references/ # AI参考资料
├── user/        # 用户文档
│   ├── guides/  # 使用指南
│   ├── tutorials/ # 教程
│   └── examples/ # 示例
├── dev/         # 开发文档
│   ├── architecture/ # 架构文档
│   ├── api/      # API文档
│   ├── roadmap/  # 开发路线
│   └── workflow/ # 开发流程
└── shared/      # 共享资源
    ├── templates/ # 文档模板
    └── glossary/  # 术语表
```

## 文档类型说明

### AI 文档

这些文档专为AI工具（如Cursor）设计，将被动态加载到AI上下文中，帮助AI理解项目结构、开发规范和工作流程。

- **prompts/**: 预定义的AI提示词模板
- **context/**: 项目上下文信息，帮助AI了解项目背景
- **rules/**: AI应遵循的规则和约束
- **references/**: 技术参考资料

### 用户文档

面向VibeCopilot的终端用户，包括非技术人员和使用AI辅助开发的开发者。

- **guides/**: 产品使用指南和最佳实践
- **tutorials/**: 分步教程，帮助用户掌握特定功能
- **examples/**: 实际使用场景和案例研究

### 开发文档

面向VibeCopilot项目的开发者和贡献者。

- **architecture/**: 系统设计和架构文档
- **api/**: API文档和接口规范
- **roadmap/**: 开发路线图和计划
- **workflow/**: 开发流程和贡献指南

### 共享资源

可被多种受众使用的通用资源。

- **templates/**: 文档和代码模板
- **glossary/**: 术语表和定义

## 文档使用指南

1. **新用户**: 从 `user/how_to_work.md` 开始了解项目
2. **开发者**: 从 `dev/architecture/` 开始了解系统设计
3. **AI工具**: 从 `ai/rules/` 开始学习项目规范

## 文档维护指南

- 所有文档应使用Markdown格式
- 每个文档应包含标准化的元数据头部
- 文档更新应与代码变更同步进行
